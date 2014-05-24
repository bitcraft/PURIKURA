#!/usr/bin/env python
"""
DBus service to share the camera object
"""
import sys
sys.path.append('/home/mjolnir/git/PURIKURA/')

import socket
import threading
import logging
import shutter
import gobject
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from six.moves import queue

from pyrikura.config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.dbus")

# dbus config
bus_name = Config.get('camera', 'dbus-name')
bus_path = Config.get('camera', 'dbus-path')

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
            host = 'localhost'
            port = Config.getint('arduino', 'tcp-port')
            while 1:
                try:
                    logger.debug('waiting for value...')
                    _value = self.queue.get(timeout=3)
                except queue.Empty:
                    logger.debug('thread timeout')
                    break
                else:
                    logger.debug('sending %s', str(_value))
                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((host, port))
                    conn.send(str(_value) + '\r\n')
                    conn.close()
                    self.queue.task_done()
            logger.debug('end of thread')
            self.thread = None

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
            self.thread.start()


class PhotoboothService(dbus.service.Object):
    """ Sharing of camera and arduino with a 'simple' api
    """
    def __init__(self):
        logger.debug('starting photobooth service...')
        name = dbus.service.BusName(bus_name, bus=dbus.SessionBus())
        super(PhotoboothService, self).__init__(name, bus_path)
        self.capture_filename = 'capture.jpg'
        self.preview_filename = 'preview.jpg'
        self._camera_lock = threading.Lock()
        self._camera = None

        self._arduino_lock = threading.Lock()
        self._arduino_handler = None

    def _open_camera(self):
        """ Open the camera for use (internal use only)

        Safe to be called more that once or while camera is already open
        """
        with self._camera_lock:
            if self._camera is None:
                try:
                    self._camera = shutter.Camera()
                    return True
                except shutter.ShutterError as e:
                    logger.debug('unable to open camera')
                    return False
            else:
                return True

    def _close_camera(self):
        """ Close the camera for use (internal use only)

        Safe to be called more that once or while camera is already closed
        """
        with self._camera_lock:
            if self._camera is None:
                return True
            else:
                try:
                    logger.debug('attempting camera.close()...')
                    self._camera.close()
                    logger.debug('attempting setting to none...')
                    self._camera = None
                    return True
                except shutter.ShutterError as e:
                    logger.debug('unable to close camera')
                    return False

    def _reset_camera(self):
        """ Reset camera by closing and opening it again (internal use only)
        """
        logger.debug('attempting to reset the camera...')
        with self._camera_lock:
            return self._close_camera() and self._open_camera()

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
    def open_camera(self):
        """ Open the camera for use

        Safe to be called more that once or while camera is already open
        """
        return self._open_camera()

    @dbus.service.method(bus_name, out_signature='b')
    def close_camera(self):
        """ Close the camera for use

        Safe to be called more that once or while camera is already closed
        """
        return self._close_camera()

    @dbus.service.method(bus_name, out_signature='b')
    def capture_preview(self):
        """ Capture a preview image and save to a file

        Returns boolean of succeeded or not
        """
        if self._camera is None:
            logger.debug('want to capture preview, but camera is not setup')
            return False

        with self._camera_lock:
            try:
                self._camera.capture_preview(self.preview_filename)
                return True
            except shutter.ShutterError as e:
                if e.result == -1:
                    logger.debug('unable to focus camera')
                else:
                    logger.debug('unhandled error {}', e.result)
                return False

    @dbus.service.method(bus_name, out_signature='b')
    def capture_image(self):
        """ Capture a full image and save to a file

        Returns boolean of succeeded or not
        """
        if self._camera is None:
            logger.debug('want to capture, but camera is not setup')
            return False

        with self._camera_lock:
            try:
                self._camera.capture_image(self.capture_filename)
                return True
            except shutter.ShutterError as e:
                if e.result == -1:
                    logger.debug('unable to focus camera')
                else:
                    logger.debug('unhandled error {}', e.result)
                return False

    @dbus.service.method(bus_name, out_signature='(bay)')
    def download_preview(self):
        """ Capture preview image and return data

        Returns dbus.Struct:
            [0] Boolean if succeeded or not
            [1] dbus.ByteArray of preview image data

        Image data will be an empty string if capture is not successful
        """
        if self._camera is None:
            logger.debug('want to get preview, but camera is not setup')
            return False

        with self._camera_lock:
            try:
                data = self._camera.capture_preview().get_data()
                return dbus.Struct((True, dbus.ByteArray(data)),
                                   signature='bay')
            except shutter.ShutterError as e:
                logger.debug('unhandled error {}', e.result)
                return dbus.Struct((False, dbus.ByteArray('')),
                                   signature='bay')

    @dbus.service.method(bus_name, out_signature='b')
    def reset(self):
        """ Reset camera by closing and opening it again
        """
        self._reset_camera()

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
    service = PhotoboothService()
    loop = gobject.MainLoop()

    logger.debug('starting gobject loop...')
    try:
        loop.run()
    except:
        loop.quit()
        raise
