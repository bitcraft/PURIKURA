#!/usr/bin/env python
"""
This program is the nuts and bolts of the photo booth.

It uses a workflow/broker hack to make a photobooth.  In relationship with
the entire project, this is all that is needed to accept input, take photos,
compose and print them.  The kiosk app can be thought of as a pretty
touch-enabled file browser.

This creates all the images that you can browse with in the kiosk app.

This configuration is used in my professional photo booth service and uses an
arduino for input.  Free free to customize.
"""
import sys
#sys.path.append('/home/mjolnir/git/PURIKURA/')
sys.path.append('/Volumes/Mac2/Users/leif/pycharm/PURIKURA/')
sys.path.append('/Volumes/Mac2/Users/leif/pycharm/PURIKURA/pyrikura')

from twisted.internet import reactor, defer, task, protocol
from twisted.protocols.basic import LineReceiver
from twisted.plugin import getPlugins, IPlugin
import threading
import os
import logging
import pygame

from pyrikura import ipyrikura
from pyrikura import resources
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
capture_image = Config.get('camera', 'capture-image')
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

# specific to the camera system i use!
dbus_name = Config.get('camera', 'dbus-name') + '.camera'
dbus_path = Config.get('camera', 'dbus-path') + '/camera'

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


class Session:
    needed_captures = Config.getint('event', 'needed-captures')
    next_countdown_delay = Config.getint('event', 'next-countdown-delay')
    countdown_interval = 1

    def __init__(self):
        logger.debug('building new session...')
        self.running = False
        self.captures = 0
        self.process_chain = []

        plugins = list(getPlugins(ipyrikura.IPyrikuraPlugin))
        p = plugins[-1]

        fc = p.new('tmp')
        self.process_chain.append(fc)

        # build a basic workflow

        #arch1 = p('FileCopy', dest=originals_path)
        #arch2 = p('FileCopy', dest=composites_path)
        #spool = p('FileCopy', dest=shared_path)
        #thumb1 = p('Thumbnailer', size='256x256', dest=thumbs_path)
        #thumb2 = p('Thumbnailer', size='1024x1024', dest=details_path)
        #comp = p('Composer', template=template_path)
        #if Config.getboolean('kiosk', 'print'):
        #    spool.subscribe(comp)
        #arch2.subscribe(comp)
        #thumb1.subscribe(arch1)
        #thumb2.subscribe(arch1)

    def successful_capture(self, result):
        self.captures += 1
        logger.debug('successful capture (%s/%s)',
                     self.captures, self.needed_captures)

        if self.captures >= self.needed_captures:
            logger.debug('finished the session')
            bell1.play()
            self.running = False
        else:
            logger.debug('finished the capture')
            finished.play()
            reactor.callLater(self.next_countdown_delay, self.capture)

        # result is a capture filename or data
        d = self.process_chain[0].process(result)

    def failed_capture(self, result):
        """ plays the error sound rapidly 3x """
        logger.debug('failed capture')
        task.deferLater(reactor, 0, error.play)
        task.deferLater(reactor, .15, error.play)
        task.deferLater(reactor, .30, error.play)

    def capture(self):
        def fake_shutter(result=None):
            return 'capture.jpg'

        # this is the countdown timer
        delay = (self.needed_captures - 1) * self.countdown_interval
        c = task.LoopingCall(bell0.play)
        task.deferLater(reactor, delay, c.stop)
        d = c.start(self.countdown_interval)

        # this is the camera trigger
        d = d.addCallback(fake_shutter)
        d.addCallback(self.successful_capture)
        #d.addErrback(self.failed_capture)
        return d

    def start(self, result=None):
        if self.running:
            logger.debug('want to start, but already running')
            return

        logger.debug('start new session')
        self.running = True
        self.captures = 0
        self.capture()


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
