#!/usr/bin/env python
"""
DBus service to share the arduino object
"""
import sys
sys.path.append('/home/mjolnir/git/PURIKURA/')

import threading
import logging
import gobject
import dbus
import dbus.service
import serial
from dbus.mainloop.glib import DBusGMainLoop
from six.moves import queue

from pyrikura.config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.dbus.arduino")

# dbus config
bus_name = Config.get('camera', 'dbus-name') + '.arduino'
bus_path = Config.get('camera', 'dbus-path') + '/arduino'

DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()


class EmitterObject(dbus.service.Object):
    def __init__(self):
        dbus.service.Object.__init__(self, bus, 'com.kilbuckcreek.photobooth')

    @dbus.service.signal(dbus_interface='com.kilbuckcreek.photobooth')
    def emit(self):
        logger.debug('got signal for session start')


class ArduinoReader(object):
    def __init__(self, port, lock):
        self.queue = queue.Queue(maxsize=255)
        self.thread = None
        self.port = port
        self.port_lock = lock
        self.running = False
        self.emmiter = EmitterObject()

    def start(self):
        def read_forever():
            while self.running:
                with self.port_lock:
                    data = self.port.read()
                    self.emmiter.emit()
                    print data

        self.running = True

    def stop(self):
        self.running = False


class ArduinoWriter(object):
    def __init__(self, port, lock):
        self.queue = queue.Queue(maxsize=255)
        self.thread = None
        self.port = port
        self.port_lock = lock
        self.running = False

    def set_camera_tilt(self, value):
        """ Set camera tilt

        TODO: some kind of smoothing.
        """
        self.queue.put(value)

    def start(self):
        def send_message():
            while 1:
                logger.debug('waiting for value...')
                value = self.queue.get()
                logger.debug('sending %s', str(value))
                try:
                    with self.port_lock:
                        self.port.write(chr(0x80) + chr(value))
                except:
                    self.queue.task_done()
                    break
                else:
                    self.queue.task_done()

            logger.debug('end of thread')
            self.thread = None

        if self.thread is None:
            logger.debug('starting serial thread')
            self.thread = threading.Thread(target=send_message)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        self.running = False


class ArduinoService(dbus.service.Object):
    """ Sharing of arduino with a 'simple' api
    """
    def __init__(self):
        logger.debug('starting photobooth service...')
        name = dbus.service.BusName(bus_name, bus=dbus.SessionBus())
        super(ArduinoService, self).__init__(name, bus_path)
        self._arduino_lock = threading.Lock()
        self._arduino_writer = None
        self._arduino_reader = None
        self.port = None
        self.port_lock = threading.Lock()

    def _open_arduino(self):
        """ Open the arduino (internal use only)
        """
        if self.port is None:
            with self._arduino_lock:
                self.port = serial.Serial(
                    Config.get('arduino', 'port'),
                    Config.getint('arduino', 'baudrate')
                )
                self._arduino_writer = ArduinoWriter(self.port, self.port_lock)
                self._arduino_reader = ArduinoReader(self.port, self.port_lock)
            return True
        else:
            return True

    def _close_arduino(self):
        """ Close the arduino (internal use only)
        """
        if self.port is not None:
            with self._arduino_lock:
                self._arduino_writer.stop()
                self._arduino_reader.stop()
                self._arduino_writer = None
                self._arduino_reader = None
                self.port.close()
                self.port = None
            return True
        else:
            return True

    def _reset_arduino(self):
        """ Reset arduino by closing and opening it again (internal use only)
        """
        logger.debug('attempting to reset the arduino...')
        with self._arduino_lock:
            return self._close_arduino() and self._open_arduino()

    @dbus.service.method(bus_name, out_signature='b')
    def reset(self):
        """ Reset arduino by closing and opening it again
        """
        self._reset_arduino()

    @dbus.service.method(bus_name, out_signature='b')
    def open_arduino(self):
        """ Open the arduino for use

        Safe to be called more that once or while arduino is already open
        """
        return self._open_arduino()

    @dbus.service.method(bus_name, out_signature='b')
    def close_arduino(self):
        """ Close the arduino

        Safe to be called more that once or while arduino is already closed
        """
        return self._close_arduino()

    @dbus.service.method(bus_name, in_signature='i', out_signature='b')
    def set_camera_tilt(self, value):
        """ Set camera tilt

        Uses the arduino for communications with servo.

        Value must be 0 or greater, but less or equal to 180.

        TODO: some kind of smoothing.
        """
        with self._arduino_lock:
            self._arduino_writer.set_camera_tilt(value)


if __name__ == '__main__':
    logger.debug('starting arduino service...')
    service = ArduinoService()
    logger.debug('starting arduino gobject main loop...')
    loop = gobject.MainLoop()

    logger.debug('starting arduino dbus loop...')
    try:
        loop.run()
    except:
        loop.quit()
        raise
