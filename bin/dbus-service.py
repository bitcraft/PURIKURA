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
from dbus import ByteArray

from pyrikura.config import Config

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
        with self._camera_lock:
            try:
                logger.debug('attempting to open camera')
                self._camera = shutter.Camera()
                return True
            except shutter.ShutterError as e:
                logger.debug('unable to open camera')
                return False

    def _close_camera(self):
        with self._camera_lock:
            try:
                logger.debug('attempting to close camera')
                self._camera = None
                return True
            except shutter.ShutterError as e:
                logger.debug('unable to close camera')
                return False

    def _reset(self):
        with self._camera_lock:
            if self._camera:
                self._camera = None
                self._open_camera()

    @dbus.service.method(bus_name, out_signature='b')
    def open_camera(self):
        return self._open_camera()

    @dbus.service.method(bus_name, out_signature='b')
    def close_camera(self):
        return self._close_camera()

    @dbus.service.method(bus_name, out_signature='b')
    def capture_preview(self):
        logger.debug('attempting to capture preview...')
        with self._camera_lock:
            try:
                self._camera.capture_image(self.preview_filename)
                return True
            except shutter.ShutterError as e:
                # couldn't focus
                if e.result == -1:
                    pass
                else:
                    self.reset()
                    self._camera.capture_image(self.preview_filename)
                return False

    @dbus.service.method(bus_name, out_signature='b')
    def capture_image(self):
        logger.debug('attempting to capture image...')
        with self._camera_lock:
            try:
                self._camera.capture_image(self.capture_filename)
                return True
            except shutter.ShutterError as e:
                # couldn't focus
                if e.result == -1:
                    pass
                else:
                    self.reset()
                    self._camera.capture_image(self.capture_filename)
                return False

    @dbus.service.method(bus_name, out_signature='ay')
    def downaload_preview(self):
        logger.debug('attempting to download preview...')
        with self._camera_lock:
            try:
                data = self._camera.capture_preview().get_data()
                return ByteArray(data)
            except shutter.ShutterError as e:
                self.reset()

    @dbus.service.method(bus_name)
    def reset(self):
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
