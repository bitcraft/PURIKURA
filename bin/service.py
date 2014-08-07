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
from twisted.protocols.basic import LineReceiver
from twisted.plugin import getPlugins, IPlugin
from six.moves import configparser
import threading
import os
import logging
import pygame

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
capture_filename = Config.get('camera', 'capture-filename')
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
bell1.set_volume(bell1.get_volume() * .6)
finished.set_volume(finished.get_volume() * .5)

def get_class(o):
    name = o.__class__.__name__
    if name.endswith('Factory'):
        return name[:-7]
    else:
        return name

class Session:
    def __init__(self):
        logger.debug('building new session...')

        p = dict((get_class(p), p) for p in 
                 getPlugins(ipyrikura.IPyrikuraPlugin))
        
        fc0 = p['FileCopy'].new(originals_path)
        fc1 = p['FileCopy'].new(composites_path)
        fc2 = p['FileCopy'].new(shared_path)
        fc3 = p['FileCopy'].new(thumbs_path)
        fc4 = p['FileCopy'].new(details_path)
        fc5 = p['FileCopy'].new(template_path)
    
        th0 = p['ImageThumb'].new(size='256x256')
        th1 = p['ImageThumb'].new(size='1024x1024')

        #cm = p['Composer'].new(template_path)

        # build a basic workflow
        if Config.getboolean('kiosk', 'print'):
            pass

        g = Graph()
        g.update(fc0, [th0, th1])
        g.update(th0, [fc3])
        g.update(th1, [fc4])
        #g.update(cm, [fc1])
        self.graph = g
        self.head = fc0

    def capture(self):
        def fake_shutter(result=None):
            return 'capture.jpg'

        interval = Config.getint('camera', 'countdown-interval')
        c = task.LoopingCall(bell0.play)
        d = c.start(interval)
        d = d.addCallback(fake_shutter)
        task.deferLater(reactor, 3 * interval, c.stop)
        return d

    @defer.inlineCallbacks 
    def start(self, result=None):
        logger.debug('start new session')

        countdown_delay = Config.getint('camera', 'countdown-delay')
        this_template = configparser.ConfigParser()
        this_template.read(template_path)
        needed_captures = template.needed_captures(this_template)
        captures = 0

        while captures < needed_captures:
            try:
                filename = yield task.deferLater(reactor, countdown_delay, self.capture)
            except:
                logger.debug('failed capture')
                task.deferLater(reactor, 0, error.play)
                task.deferLater(reactor, .15, error.play)
                task.deferLater(reactor, .30, error.play)
                continue

            captures += 1
            logger.debug('successful capture (%s/%s)',
                         captures, needed_captures)

            if captures < needed_captures: 
                finished.play()

        bell1.play()
        logger.debug('finished the session')


class Arduino(LineReceiver):
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


class ServoServiceProtocol(LineReceiver):
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
    reactor.callWhenRunning(session.start)
    logger.debug('starting service reactor...')
    try:
        reactor.run()
    except:
        reactor.stop()
        raise
