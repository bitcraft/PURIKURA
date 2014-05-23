#!/usr/bin/env python
"""
DBus service to share the camera object
"""
import sys
sys.path.append('/home/mjolnir/git/PURIKURA/')

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
        self._arduino_lock = threading.lock*()
        self._arduino_conn = None
        self._arduino_thread = None
        self._arduino_queue = None

    def _open_camera(self):
        """ Open the camera for use (internal use only)

        Safe to be called more that once or while camera is already open
        """
        logger.debug('attempting to open the camera...')
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
        logger.debug('attempting to close the camera...')
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

    def _open_arduino(self, conn):
        """ Open the arduino (internal use only)
        """
        logger.debug('attempting to open the arduino...')
        # HACK!
        if self._arduino_thread:
            self._arduino_thread.stop()
        self._arduino_thread = None
        self._arduino_queue = queue.Queue(maxsize=10)
        with self._arduino_lock:
            self._arduino_conn = conn
            return True

    def _close_arduino(self):
        """ Close the arduino (internal use only)
        """
        # HACK!
        logger.debug('attempting to close the arduino...')
        if self._arduino_thread:
            self._arduino_thread.stop()
        self._arduino_thread = None
        self._arduino_queue = None
        with self.arduino_lock:
            self._arduino_conn = None
            return True

    def _reset_arduino(self):
        """ Reset arduino by closing and opening it again (internal use only)
        """
        logger.debug('attempting to reset the arduino...')
        with self._camera_lock:
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
        logger.debug('attempting to capture preview...')
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
        logger.debug('attempting to capture image...')
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
        logger.debug('attempting to download preview...')
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

    @dbus.service.method(bus_name, in_signature='i', out_signature='b')
    def set_camera_tilt(self, value):
        """ Set camera tilt

        Uses the arduino for communications with servo.

        Value must be 0 or greater, but less or equal to 180.

        TODO: some kind of smoothing.
        """
        def send_serial():
            while 1:
                try:
                    _value = self._arduino_queue.get(timeout=1)
                except queue.Empty:
                    break
                with self._arduino_lock:
                    self._arduino_conn.sendCommand(0x80, int(_value))
                self._arduino_queue.task_done()
            self._arduino_thread = None

        try:
            self._arduino_queue.put(value, block=False)
        except queue.Full:
            try:
                self._arduino_queue.get()
                self._arduino_queue.put(value, block=False)
            except (queue.Full, queue.Empty):
                pass

        if self._arduino_thread is None:
            self._arduino_thread = threading.Thread(target=send_serial)
            self._arduino_thread.start()


if __name__ == '__main__':
    service = PhotoboothService()
    loop = gobject.MainLoop()

    logger.debug('starting gobject loop...')
    try:
        loop.run()
    except:
        loop.quit()
        raise
