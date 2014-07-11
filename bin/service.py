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
sys.path.append('/home/mjolnir/git/PURIKURA/')

import os
import logging
import pygame
import dbus

from twisted.internet import reactor, defer, task

from twisted.internet import glib2reactor
glib2reactor.install()

import dbus, gobject
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

import yapsy
from yapsy.PluginManager import PluginManager
logging.getLogger('yapsy').setLevel(logging.DEBUG)

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
dbus_name = Config.get('camera', 'dbus-name')
dbus_path = Config.get('camera', 'dbus-path')

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


class CameraTrigger:
    def __init__(self):
        try:
            bus = dbus.SessionBus()
            pb_obj = bus.get_object(dbus_name, dbus_path)
            self.iface = dbus.Interface(pb_obj, dbus_interface=dbus_name)
        except dbus.exceptions.DBusException:
            logger.error('cannot find dbus service')
            raise

        self.iface.open_camera()
        self.d = None

    def __call__(self):
        logger.debug('calling the camera trigger')
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
        logger.debug('cameratrigger.trigger')
        self.d = defer.Deferred()
        reactor.callLater(1, self)
        return self.d


class Session:
    needed_captures = Config.getint('event', 'needed-captures')
    next_countdown_delay = Config.getint('event', 'next-countdown-delay')
    countdown_interval = 1

    def __init__(self):
        logger.debug('building new session...')

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

        if Config.getboolean('kiosk', 'print'):
            spool.subscribe(comp)

        arch2.subscribe(comp)
        thumb1.subscribe(arch1)
        thumb2.subscribe(arch1)

        self.comp = comp
        self.arch1 = arch1

    def successful_capture(self, result):
        self.captures += 1
        logger.debug('successful capture (%s/%s)',
                     self.captures, self.needed_captures)

        if self.captures == self.needed_captures:
            logger.debug('finished the session')
            bell1.play()
        else:
            logger.debug('finished the capture')
            finished.play()

        self.comp.process(capture_image)
        self.arch1.process(capture_image)

    def failed_capture(self, result):
        """ plays the error sound rapidly 3x """
        logger.debug('failed capture')
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
        logger.debug('start new session')
        cam = CameraTrigger()

        d = self.countdown()
        d = d.addCallback(cam.trigger)
        d.addCallback(self.successful_capture)
        d.addErrback(self.failed_capture)
        d.addCallback(self.schedule_next)

    def start(self, result=None):
        if self.running:
            logger.debug('want to start, but already running')
            return

        self.running = True
        self.captures = 0
        self.do_session()


if __name__ == '__main__':
    def main():
        try:
            bus = dbus.SessionBus()
            bus.add_signal_reciever(session.start,
                dbus_interface='com.kilbuckcreek.photobooth',
                signal_name='startSession')
        except:
            reactor.stop()
            raise

    logger.debug('starting')
    session = Session()

    logger.debug('starting service reactor...')
    reactor.callWhenRunning(main)
    try:
        reactor.run()
    except:
        reactor.stop()
        raise
