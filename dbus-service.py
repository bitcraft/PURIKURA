"""
DBus service to share the camera object
"""
import threading
import time
import gobject
import dbus
import shutter
from StringIO import StringIO
from dbus.service import Object
from dbus.mainloop.glib import DBusGMainLoop
from dbus import ByteArray


DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()

class PhotoboothService(dbus.service.Object):
    def __init__(self):
        name = dbus.service.BusName('com.kilbuckcreek.photobooth', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, name, '/com/kilbuckcreek/photobooth')

        self._filename = 'capture.jpg'
        self._locked = True
        self.camera = None
        self.reset()
        self.do_preview = False
        self_key = None

    @dbus.service.method('com.kilbuckcreek.photobooth', out_signature='b')
    def capture_preview(self):
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

    @dbus.service.method('com.kilbuckcreek.photobooth', out_signature='b')
    def capture_image(self):
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

    @dbus.service.method('com.kilbuckcreek.photobooth', out_signature='b')
    def preview_running(self):
        return self.do_preview

    @dbus.service.method('com.kilbuckcreek.photobooth', out_signature='b')
    def preview_safe(self):
        return not self.preview_lock

    @dbus.service.signal('com.kilbuckcreek.photobooth')
    def preview_updated(self, value):
        pass

    @dbus.service.method('com.kilbuckcreek.photobooth')
    def stop_preview(self, key=None):
        if self._key == key:
            self.do_preview = False
            gobject.source_remove(self.timer)

    @dbus.service.method('com.kilbuckcreek.photobooth')
    def start_preview(self, key=None):
        self._key = key
        self.do_preview = True
        self.download_preview()
        self.timer = gobject.timeout_add(300, self.download_preview)

    @dbus.service.method('com.kilbuckcreek.photobooth', out_signature='ay')
    def get_preview(self):
        if self._locked and self.do_preview:
            try:
               data = self.camera.capture_preview().get_data()
               return ByteArray(data)
            except shutter.ShutterError as e:
                self.reset()

    @dbus.service.method('com.kilbuckcreek.photobooth', out_signature='b')
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
        self.camera = shutter.camera()
        g_camera = self.camera

    def release_camera(self):
        self._locked = False
        self.camera = None

    def reset(self):
        if self.camera:
            self.camera.exit()
        self.release_camera()
        self.open_and_lock_camera()

    @dbus.service.method('com.kilbuckcreek.photobooth')
    def do_reset(self):
        self.reset()


if __name__ == '__main__':
    service = PhotoboothService()
    loop = gobject.MainLoop()

    try:
        loop.run()
    except:
        service.camera = None
        raise
