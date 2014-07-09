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


class ArduinoHandler(object):
    def __init__(self):
        self.queue = queue.Queue(maxsize=4)
        self.lock = threading.Lock()
        self.thread = None

    def set_camera_tilt(self, value):
        """ Set camera tilt

        TODO: some kind of smoothing.
        """
        def send_message():
            while 1:
                try:
                    logger.debug('waiting for value...')
                    _value = self.queue.get(timeout=1)
                except queue.Empty:
                    logger.debug('thread timeout')
                    break
                else:
                    logger.debug('sending %s', str(_value))
                    try:
                        #write to serial port
                        #conn.send(str(_value) + '\r\n')
                        self.queue.task_done()
                    except:
                        break

            logger.debug('closing connection')
            try:
                #conn.send(str(-1) + '\r\n')
            except:
                pass

            logger.debug('end of thread')
            self.thread = None
            return

        try:
            logger.debug('adding value to arduino queue')
            self.queue.put(value, block=False)

        except queue.Full:
            logger.debug('arduino queue is full')
            try:
                self.queue.get()
                self.queue.put(value, block=False)
            except (queue.Full, queue.Empty):
                logger.debug('got some error with arduino queue')
                pass

        if self.thread is None:
            logger.debug('starting socket thread')
            self.thread = threading.Thread(target=send_message)
            self.thread.daemon = True
            self.thread.start()

class ArduinoService(dbus.service.Object):
    """ Sharing of arduino with a 'simple' api
    """
    def __init__(self):
        logger.debug('starting photobooth service...')
        name = dbus.service.BusName(bus_name, bus=dbus.SessionBus())
        super(ArduinoService, self).__init__(name, bus_path)
        self._arduino_lock = threading.Lock()
        self._arduino_handler = None

    def _open_arduino(self):
        """ Open the arduino (internal use only)
        """
        with self._arduino_lock:
            self._arduino_handler = ArduinoHandler()
        return True

    def _close_arduino(self):
        """ Close the arduino (internal use only)
        """
        with self._arduino_lock:
            self._arduino_handler = None
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
            self._arduino_handler.set_camera_tilt(value)


if __name__ == '__main__':
    service = ArduinoService()
    loop = gobject.MainLoop()

    logger.debug('starting gobject loop...')
    try:
        loop.run()
    except:
        loop.quit()
        raise