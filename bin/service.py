#!/usr/bin/env python
"""
This program is the nuts and bolts of the photo booth.

It uses the workflow/broker system to make a photobooth.  In relationship with
then entire project, this is all that is needed to accept input, take photos,
compose and print them.  The kiosk app can be thought of as a pretty
touch-enabled file browser.

This, on the other hand, creates all the images that you can browse with in the
kiosk app.

This configuration is used in my professional photo booth service and uses an
arduino for input.  Free free to customize.
"""
import os
import logging

from twisted.internet import reactor, defer, task
from twisted.protocols.basic import LineReceiver
from twisted.internet.serialport import SerialPort
import pygame

from yapsy.PluginManager import PluginManager
import dbus
import serial

from pyrikura import resources
from pyrikura.config import Config

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

# specific to arduino!
arduino_port = Config.get('arduino', 'port')
arduino_baudrate = Config.getint('arduino', 'baudrate')

# specific to the camera system i use!
dbus_name = Config.get('camera', 'dbus-name')
dbus_path = Config.get('camera', 'dbus-path')

# load all the stuff
resources.load()

# i'm lazy!
bell0 = resources.sounds['bell0']
bell1 = resources.sounds['bell1']
error = resources.sounds['error']
finished = resources.sounds['finished']

# override volumes a bit
bell1.set_volume(.5)
finished.set_volume(0.4)


class CameraTrigger:
    def __init__(self):
        bus = dbus.SessionBus()
        pb_obj = bus.get_object(dbus_name, dbus_path)
        self.iface = dbus.Interface(pb_obj, dbus_interface=dbus_name)
        self.d = None

    def __call__(self):
        if self.d is None:
            return

        d = self.d
        self.d = None
        result = self.iface.capture_image()
        if result:
            d.callback(result)
        else:
            d.errback(Exception('Camera not focused'))

    def trigger(self, result):
        self.d = defer.Deferred()
        reactor.callLater(1, self)
        return self.d


class Session:
    needed_captures = 4
    next_countdown_delay = 4
    countdown_interval = 1

    def __init__(self):
        def p(name, *arg, **kwarg):
            plugin = pm.getPluginByName(name)
            if not plugin:
                msg = "cannot load plugin {}".format(plugin)
                logger.error(msg)
                raise ValueError
            return plugin.plugin_object.new(*arg, **kwarg)

        self.running = False
        self.captures = 0

        pm = PluginManager()
        pm.setPluginPlaces([plugins_path])
        pm.collectPlugins()

        for pi in pm.getAllPlugins():
            pm.activatePluginByName(pi.name)

        arch1 = p('FileCopy', dest=originals_path)
        arch2 = p('FileCopy', dest=composites_path)
        spool = p('FileCopy', dest=shared_path)

        thumb1 = p('Thumbnailer', size='256x256', dest=thumbs_path)
        thumb2 = p('Thumbnailer', size='1024x1024', dest=details_path)

        comp = p('Composer', template=template_path)

        spool.subscribe(comp)
        arch2.subscribe(comp)
        thumb1.subscribe(arch1)
        thumb2.subscribe(arch1)

        self.comp = comp
        self.arch1 = arch1

    def successful_capture(self, result):
        self.captures += 1

        if self.captures == self.needed_captures:
            bell1.play()
        else:
            finished.play()

        self.comp.process(capture_image)
        self.arch1.process(capture_image)

    def failed_capture(self, result):
        """ plays the error sound rapidly 3x """
        task.deferLater(reactor, 0, error.play)
        task.deferLater(reactor, .15, error.play)
        task.deferLater(reactor, .30, error.play)

    def countdown(self):
        c = task.LoopingCall(bell0.play)
        delay = (self.needed_captures - 1) * self.countdown_interval
        task.deferLater(reactor, delay, c.stop)
        d = c.start(self.countdown_interval)
        return d

    def schedule_next(self, result):
        if self.captures < self.needed_captures:
            d = defer.Deferred()
            reactor.callLater(self.next_countdown_delay, self.do_session)
            return d
        else:
            self.running = False

    def do_session(self, result=None):
        cam = CameraTrigger()

        d = self.countdown()
        d = d.addCallback(cam.trigger)
        d.addCallback(self.successful_capture)
        d.addErrback(self.failed_capture)
        d.addCallback(self.schedule_next)

    def start(self, result=None):
        if self.running:
            return

        self.running = True
        self.captures = 0
        self.do_session()


class Arduino(LineReceiver):
    """
    protocol:

    0x01: trigger
    0x80: set servo
    """

    def __init__(self, session):
        self.setRawMode()
        self.session = session
        self._buf = []

    def process(self, cmd, arg):
        if cmd == 1:
            self.session.start()

    def rawDataReceived(self, data):
        for i in data:
            self._buf.append(i)

        if len(self._buf) == 2:
            cmd, arg = [ord(i) for i in self._buf]
            self.process(cmd, arg)
            self._buf = []

        # if somehow we are out of sync, then just drop all data
        elif len(self._buf) > 2:
            self._buf = []
            #session.start()


if __name__ == '__main__':
    session = Session()

    # WARNING!  Arduino stuff here
    try:
        s = SerialPort(Arduino(session), arduino_port, reactor,
                       baudrate=arduino_baudrate)
    except serial.serialutil.SerialException:
        raise

    reactor.run()
