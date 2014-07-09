#!/usr/bin/env python
"""
DBus service to share the camera object
"""
import sys
sys.path.append('/home/mjolnir/git/PURIKURA/')

import threading
import logging
import shutter

from twisted.internet import reactor, defer
from tx.dbus import client, objects, error
from tx.dbus.interface import DBusInterface, Method

from pyrikura.config import Config


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.dbus.camera")

# dbus config
bus_name = Config.get('camera', 'dbus-name') + '.camera'
bus_path = Config.get('camera', 'dbus-path') + '/camera'


class CameraService(objects.DBusObject):
    """ Sharing of camera with a 'simple' api
    """
    iface = DBusInterface(bus_name,
        Method('open', returns='b'),
        Method('close', returns='b'),
        Method('capture_preview', returns='b'),
        Method('capture_image', returns='b'),
        Method('download_preview', returns='(bay)'))

    dbusInterfaces = [iface]

    def __init__(self):
        logger.debug('starting camera service...')
        super(CameraService, self).__init__(bus_path)
        self.capture_filename = 'capture.jpg'
        self.preview_filename = 'preview.jpg'
        self._camera_lock = threading.Lock()
        self._camera = None

    def _open(self):
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

    def _close(self):
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

    def _reset(self):
        """ Reset camera by closing and opening it again (internal use only)
        """
        logger.debug('attempting to reset the camera...')
        with self._camera_lock:
            return self._close_camera() and self._open_camera()

    def dbus_open(self):
        """ Open the camera for use

        Safe to be called more that once or while camera is already open
        """
        return self._open_camera()

    def dbus_close(self):
        """ Close the camera for use

        Safe to be called more that once or while camera is already closed
        """
        return self._close_camera()

    def dbus_capture_preview(self):
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

    def dbus_capture_image(self):
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

    def dbus_download_preview(self):
        """ Capture preview image and return data

        Returns dbus.Struct:
            [0] Boolean if succeeded or not
            [1] dbus.ByteArray of preview image data

        Image data will be an empty string if capture is not successful
        """
        if self._camera is None:
            logger.debug('want to get preview, but camera is not setup')
            return False, ''

        with self._camera_lock:
            try:
                data = self._camera.capture_preview().get_data()
                return True, data
            except shutter.ShutterError as e:
                logger.debug('unhandled error %s: %s', e.result, e.message)
                return False, ''

    def dbus_reset(self):
        """ Reset camera by closing and opening it again
        """
        return self._reset_camera()


@defer.inlineCallbacks
def main():
    logger.debug('exporting camera dbus interface...')
    try:
        conn = yield client.connect(reactor)
        conn.exportObject(CameraService(bus_path))
        yield conn.requestBusName(bus_name)
    except error.DBusException, e:
        logger.error('failed to export camera dbus interface')
        reactor.stop()


if __name__ == '__main__':
    reactor.callWhenRunning(main)
    reactor.run()
