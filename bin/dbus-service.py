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

from pyrikura.config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.dbus")

# dbus config
bus_name = Config.get('camera', 'dbus-name')
bus_path = Config.get('camera', 'dbus-path')

DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()


class PhotoboothService(dbus.service.Object):
    def __init__(self):
        logger.debug('starting photobooth service...')
        name = dbus.service.BusName(bus_name, bus=dbus.SessionBus())
        super(PhotoboothService, self).__init__(name, bus_path)
        self.capture_filename = 'capture.jpg'
        self.preview_filename = 'preview.jpg'
        self._camera_lock = threading.Lock()
        self._camera = None

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

    def _reset(self):
        """ Reset camera by closing and opening it again (internal use only)
        """
        logger.debug('attempting to reset the camera...')
        with self._camera_lock:
            return self._close_camera() and self._open_camera()

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

    @dbus.service.method(bus_name)
    def reset(self):
        """ Reset camera by closing and opening it again
        """
        self._reset()


if __name__ == '__main__':
    service = PhotoboothService()
    loop = gobject.MainLoop()

    logger.debug('starting gobject loop...')
    try:
        loop.run()
    except:
        loop.quit()
        raise
