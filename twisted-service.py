from twisted.internet import reactor, base, defer, threads, task
from twisted.protocols.basic import LineReceiver
from twisted.internet.serialport import SerialPort
from yapsy.PluginManager import PluginManager 
import os
import dbus
import pygame
import serial


event = 'test'

settings = {}
settings['bell0_sound'] = os.path.join('sounds', 'bell.wav')
settings['bell1_sound'] = os.path.join('sounds', 'long_bell.wav')
settings['error_sound'] = os.path.join('sounds', 'error.wav')
settings['next_sound'] = os.path.join('sounds', 'whistle.wav')
settings['printsrv']   = '/home/mjolnir/smb-printsrv'
settings['template']   = 'templates/2x6vintage.template'
settings['thumbnails'] = '/home/mjolnir/events/{}/small'.format(event)
settings['detail']     = '/home/mjolnir/events/{}/medium'.format(event)
settings['originals']  = '/home/mjolnir/events/{}/originals'.format(event)
settings['composites'] = '/home/mjolnir/events/{}/composites/'.format(event)
settings['temp_image'] = 'capture.jpg'

paths = ('thumbnails', 'detail', 'originals', 'composites')

pygame.mixer.init()

bell0 = pygame.mixer.Sound(settings['bell0_sound'])
bell1 = pygame.mixer.Sound(settings['bell1_sound'])
error = pygame.mixer.Sound(settings['error_sound'])
whistle = pygame.mixer.Sound(settings['next_sound'])


class CameraTrigger:
    if_name = 'com.kilbuckcreek.photobooth'
    if_url = '/com/kilbuckcreek/photobooth'

    def __init__(self, iface):
        bus = dbus.SessionBus()
        pb_obj = bus.get_object(self.if_name, self.if_url)
        pb_iface = dbus.Interface(pb_obj, dbus_interface=self.if_name)
        self._iface = pb_iface

    def __call__(self):
        if self.d is None:
            return

        d = self.d
        self.d = None
        result = self._iface.capture_image() 
        if result:
            d.callback(result)
        else:
            d.errback(Exception('Camera not focused'))
        
    def trigger(self, result):
        self.d = defer.Deferred()
        reactor.callLater(1, self)
        return self.d


class Session:
    running = False
    needed_captures = 4
    next_countdown_delay = 4
    countdown_interval = 1

    def __init__(self):
        def p(name, *arg, **kwarg):
            plugin = pm.getPluginByName(name)
            if not plugin:
                raise ValueError, "cannot load plugin {}".format(self.plugin_name)
            return plugin.plugin_object.new(*arg, **kwarg)

        pm = PluginManager() 
        pm.setPluginPlaces(['./pyrikura/plugins']) 
        pm.collectPlugins() 

        for pi in pm.getAllPlugins(): 
            pm.activatePluginByName(pi.name) 

        arch1 = p('FileCopy', dest=settings['originals'])
        arch2 = p('FileCopy', dest=settings['composites'])
        spool = p('FileCopy', dest=settings['printsrv'])

        thumb1 = p('Thumbnailer', size='256x256', dest=settings['thumbnails'])
        thumb2 = p('Thumbnailer', size='1024x1024', dest=settings['detail'])

        comp = p('Composer', template=settings['template'])

        spool.subscribe(comp)
        arch2.subscribe(comp)

        thumb1.subscribe(arch1)
        thumb2.subscribe(arch1)

        self.comp = comp
        self.arch1 = arch1

    def sucessful_capture(self, result):
        self.captures += 1

        if self.captures == self.needed_captures:
            bell1.set_volume(.5)
            bell1.play()
        else:
            whistle.set_volume(0.4)
            whistle.play()

        self.comp.process('capture.jpg')
        self.arch1.process('capture.jpg')

    def failed_capture(self, result):
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
        cam = CameraTrigger(self._iface)

        d = self.countdown()
        d = d.addCallback(cam.trigger)
        d.addCallback(self.sucessful_capture)
        d.addErrback(self.failed_capture)
        d.addCallback(self.schedule_next)

    def start(self, result=None):
        if self.running:
            return

        self.running = True
        self.captures = 0
        self.do_session()


class Arduino(LineReceiver):
    def __init__(self):
        self.setRawMode()
        self.clearLineBuffer()
        self._buffer = ''

    def rawDataReceived(self, data):
        self._buffer += data

        if len(self._buffer) >= 2:
            for i in self._buffer:
                print ord(i)
            self._buffer = ''

        #session.start()


if __name__ == '__main__':
    session = Session()
    port, baudrate = '/dev/ttyACM0', 9600
        
    try:
        s = SerialPort(Arduino(), port, reactor, baudrate=baudrate)
    except serial.serialutil.SerialException:
        raise

    reactor.run()
