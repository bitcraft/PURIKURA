#!/usr/bin/env python
"""
This program is the nuts and bolts of the photo booth.
"""
import sys
sys.path.append('/home/mjolnir/git/PURIKURA/')
sys.path.append('/home/mjolnir/git/PURIKURA/pyrikura')
#sys.path.append('/Volumes/Mac2/Users/leif/pycharm/PURIKURA/')
#sys.path.append('/Volumes/Mac2/Users/leif/pycharm/PURIKURA/pyrikura')

from twisted.internet import reactor, defer, task, protocol
from twisted.internet.serialport import SerialPort
from twisted.protocols import basic
from twisted.plugin import getPlugins, IPlugin
from zope.interface.verify import verifyObject
from six.moves import configparser
import zope.interface.exceptions
import serial
import traceback
import threading
import logging
import pygame
import os
import re

from pyrikura import ipyrikura
from pyrikura import resources
from pyrikura import template
from pyrikura.graph import Graph
from pyrikura.config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.booth")

# because i hate typing
jpath = os.path.join

# paths
app_root_path = Config.get('paths', 'root')
app_config_path = jpath(app_root_path, 'config')
app_resources_path = jpath(app_root_path, 'resources')
app_sounds_path = jpath(app_resources_path, 'sounds')
app_images_path = jpath(app_resources_path, 'images')
all_templates_path = jpath(app_resources_path, 'templates')
all_images_path = Config.get('paths', 'images')
shared_path = Config.get('paths', 'shared')
plugins_path = Config.get('paths', 'plugins')

# event paths
event_name = Config.get('event', 'name')
template_path = jpath(all_templates_path, Config.get('event', 'template'))
event_images_path = jpath(all_images_path, event_name)
thumbs_path = jpath(event_images_path, 'thumbnails')
details_path = jpath(event_images_path, 'detail')
originals_path = jpath(event_images_path, 'originals')
composites_path = jpath(event_images_path, 'composites')
paths = ('thumbnails', 'detail', 'originals', 'composites')

# make sure directory structure is usuable                                                                                 
if Config.get('paths', 'make-images-path'):
    for d in (thumbs_path, details_path, originals_path, composites_path):
        try:
            isdir = os.path.isdir(d)
        except:
            raise
        if not isdir:
            os.makedirs(d, 0755)

# mixer must be initialized before sounds will play
pygame.mixer.init(frequency=Config.getint('sound', 'mixer-frequency'),
                  buffer=Config.getint('sound', 'mixer-buffer'))

# load all the stuff
resources.load()

# i'm lazy!
bell0 = resources.sounds['bell0']
bell1 = resources.sounds['bell1']
error = resources.sounds['error']
finished = resources.sounds['finished']

# manage volumes a bit
bell1.set_volume(bell1.get_volume() * .9)
finished.set_volume(finished.get_volume() * .8)

def get_class(o):
    name = o.__class__.__name__
    if name.endswith('Factory'):
        return name[:-7]
    else:
        return name

class Session:
    def __init__(self):
        logger.debug('building new session...')

        self.template = configparser.ConfigParser()
        self.template.read(template_path)
        self.camera = None

        p = dict((get_class(p), p) for p in 
                 getPlugins(ipyrikura.IPyrikuraPlugin))
        
        for name in p.keys():
            logger.debug("loaded plugin %s", name)

        self.camera = p['ShutterCamera'].new(
                re.compile(Config.get('camera', 'name')))

        fc0 = p['FileCopy'].new(originals_path)
        fc1 = p['FileCopy'].new(composites_path, delete=True)
        fc3 = p['FileCopy'].new(thumbs_path)
        fc4 = p['FileCopy'].new(details_path)
        fc5 = p['FileCopy'].new(template_path)
        spool = p['FileCopy'].new(shared_path)
    
        th0 = p['ImageThumb'].new(size='256x256', destination='thumbnail.png')
        th1 = p['ImageThumb'].new(size='1024x1024', destination='thumbnail.png')

        cm = p['Composer'].new(self.template)
        fd0 = p['FileDelete'].new()
        fd1 = p['FileDelete'].new()

        # build a basic workflow
        if Config.getboolean('kiosk', 'print'):
            pass

        g = Graph()
        g.update(fc0, [th0, th1])
        #g.update(fc0, [cm, th0, th1])
        g.update(cm,  [fc1, fd1])
        g.update(th0, [fc3])
        g.update(th1, [fc4])
        self.graph = g
        self.head = fc0
        self.chain = None

    def capture(self):
        def shutter(result=None):
            d = self.camera.capture_image()
            return d

        interval = Config.getint('camera', 'countdown-interval')
        c = task.LoopingCall(bell0.play)
        d = c.start(interval)
        d = d.addCallback(shutter)
        task.deferLater(reactor, 3 * interval, c.stop)
        return d

    @defer.inlineCallbacks 
    def start(self, result=None):
        logger.debug('start new session')

        countdown_delay = Config.getint('camera', 'countdown-delay')
        needed_captures = template.needed_captures(self.template)
        captures = 0
        errors = 0

        while captures < needed_captures and errors < 3:
            try:
                filename = yield task.deferLater(reactor, countdown_delay, self.capture)
            except:
                traceback.print_exc(file=sys.stdout)
                errors += 1
                logger.debug('failed capture %s/3', errors)
                task.deferLater(reactor, 0, error.play)
                task.deferLater(reactor, .15, error.play)
                task.deferLater(reactor, .30, error.play)
                continue

            captures += 1
            errors = 0
            logger.debug('successful capture (%s/%s)',
                         captures, needed_captures)

            if captures < needed_captures: 
                finished.play()

            # start processing chain
            chain = self.graph.search(self.head)

            r = dict()
            def log(result, plugin, parent=None):
                if parent:
                    print "---->", get_class(parent), get_class(plugin), result
                else:
                    print "====>", get_class(plugin), result
                return result


            # build callback chain
            dd = dict()
            parent, head_plugin = next(chain)
            head_deferred = defer.Deferred()
            head_deferred.addCallback(head_plugin.process)
            dd[head_plugin] = head_deferred
            print "    >", None, get_class(head_plugin)

            def err(fail):
                print "error!"
                #print fail

            for parent, plugin in chain:
                print "    >", get_class(parent), get_class(plugin)

                d = defer.Deferred()
                d.addCallback(log, plugin, parent)
                d.addCallbacks(plugin.process, err)
                dd[plugin] = d

                #dd[parent].addCallback(d.callback)
                #d.chainDeferred(dd[parent])
                dd[parent].chainDeferred(d)

            head_deferred.callback(filename)
                
        bell1.play()
        logger.debug('finished the session')


class Arduino(basic.LineReceiver):
    """
    protocol:

    0x01: trigger
    0x80: set servo
    """
    def __init__(self, session):
        logger.debug('new arduino')
        self.session = session
        self.lock = threading.Lock()

    def process(self, cmd, arg):
        logger.debug('processing for arduino: %s %s', cmd, arg)
        if cmd == 1 and arg == 2:
            self.session.start()

    def sendCommand(self, cmd, arg):
        logger.debug('sending to arduino: %s %s', cmd, arg)
        data = chr(cmd) + chr(arg)
        self.transport.write(data)

    def lineReceived(self, data):
        logger.debug('got serial data %s', data)
        try:
            cmd, arg = [int(i) for i in data.split()]
            logger.debug('got command %s %s', cmd, arg)
            self.process(cmd, arg)
        except ValueError:
            logger.debug('unable to parse: %s', data)
            raise


class ServoServiceProtocol(basic.LineReceiver):
    def lineReceived(self, data):
        logger.debug('got remote data %s', data)
        value = None

        try:
            value = int(data)
        except ValueError:
            logger.debug('cannot process data %s', data)

        if value == -1:
            self.transport.loseConnection()
            return

        else:
            try:
                self.factory.arduino.sendCommand(0x80, value)
            except:
                logger.debug('problem communicating with arduino')
                raise


class ServoServiceFactory(protocol.ServerFactory):
    protocol = ServoServiceProtocol

    def __init__(self, arduino):
        self._arduino = arduino

    @property
    def arduino(self):
        return self._arduino


if __name__ == '__main__':
    logger.debug('starting photo booth service')
    session = Session()
    arduino = Arduino(session)
    #reactor.callWhenRunning(session.start)

    try:
        s = SerialPort(arduino, Config.get('arduino', 'port'), reactor,
        baudrate=Config.getint('arduino', 'baudrate'))
    except serial.serialutil.SerialException:
        raise

    # arduino servo tilt server
    reactor.listenTCP(Config.getint('arduino', 'tcp-port'),
        ServoServiceFactory(arduino))

    # preview frame producer
    preview_port = 23453
    factory = protocol.Factory()
    factory.protocol = session.camera.create_producer
    reactor.listenTCP(preview_port, factory)

    logger.debug('starting service reactor...')
    try:
        reactor.run()
    except:
        reactor.stop()
        raise
