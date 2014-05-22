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
        self._filename = 'capture.jpg'
        self.camera_lock = threading.Lock()
        self.camera = None
        self.reset()
        self.do_preview = False

    @dbus.service.method(bus_name, out_signature='b')
    def capture_preview(self):
        logger.debug('capturing preview...')
        if self._locked:
            try:
                self.camera.capture_image('preview.jpg')
                return True
            except shutter.ShutterError as e:
                # couldn't focus
                if e.result == -1:
                    pass
                else:
                    self.reset()
                    self.camera.capture_image('preview.jpg')
                return False

        return False

    @dbus.service.method(bus_name, out_signature='b')
    def capture_image(self):
        logger.debug('capturing image...')
        if self._locked:
            try:
                self.camera.capture_image(self._filename)
                return True
            except shutter.ShutterError as e:
                # couldn't focus
                if e.result == -1:
                    pass
                else:
                    self.reset()
                    self.camera.capture_image(self._filename)
                return False

        return False

    @dbus.service.method(bus_name, out_signature='b')
    def preview_running(self):
        return self.do_preview

    @dbus.service.method(bus_name, out_signature='b')
    def preview_safe(self):
        return not self.preview_lock

    @dbus.service.signal(bus_name)
    def preview_updated(self, value):
        pass

    @dbus.service.method(bus_name)
    def stop_preview(self, key=None):
        if self._key == key:
            self.do_preview = False
            gobject.source_remove(self.timer)

    @dbus.service.method(bus_name)
    def start_preview(self, key=None):
        self._key = key
        self.do_preview = True
        self.download_preview()
        self.timer = gobject.timeout_add(300, self.download_preview)

    @dbus.service.method(bus_name, out_signature='ay')
    def get_preview(self):
        if self._locked and self.do_preview:
            try:
                data = self.camera.capture_preview().get_data()
                return ByteArray(data)
            except shutter.ShutterError as e:
                self.reset()

    @dbus.service.method(bus_name, out_signature='b')
    def download_preview(self):
        if self._locked:
            try:
                self.camera.capture_preview('preview.jpg')
                return True
            except shutter.ShutterError as e:
                self.reset()
                return False

        return True

    def open_and_lock_camera(self):
        if self._locked:
            raise Exception
        self._locked = True
        self.camera = shutter.Camera()
        g_camera = self.camera

    def release_camera(self):
        self._locked = False
        self.camera = None

    def reset(self):
        if self.camera:
            self.camera.exit()
        self.release_camera()
        self.open_and_lock_camera()

    @dbus.service.method(bus_name)
    def do_reset(self):
        self.reset()


if __name__ == '__main__':
    service = PhotoboothService()
    loop = gobject.MainLoop()

    logger.debug('starting gobject loop...')
    try:
        loop.run()
    except:
        loop.quit()
        raise
