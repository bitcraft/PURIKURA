"""
DBus service to share the camera object!
"""
import dbus
import gobject
import piggyphoto
import time
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

    @dbus.service.method('com.kilbuckcreek.photobooth', out_signature='b')
    def capture_image(self):
        if self._locked:
            try:
                self.camera.capture_image(self._filename)
                return True
            except piggyphoto.libgphoto2error as e:
                # couldn't focus
                if e.result == -1:
                    pass
                else:
                    self.reset()
                    self.camera.capture_image(self._filename)
                return False

    @dbus.service.method('com.kilbuckcreek.photobooth', out_signature='b')
    def preview_safe(self):
        return not self.preview_lock

    @dbus.service.signal('com.kilbuckcreek.photobooth')
    def preview_updated(self, value):
        pass

    @dbus.service.method('com.kilbuckcreek.photobooth')
    def stop_preview(self):
        self.do_preview = False
        gobject.source_remove(self.timer)

    @dbus.service.method('com.kilbuckcreek.photobooth')
    def start_preview(self):
        self.do_preview = True
        self.timer = gobject.timeout_add(500, self.download_preview)

    @dbus.service.method('com.kilbuckcreek.photobooth', out_signature='ay')
    def get_preview(self):
        if self._locked and self.do_preview:
            try:
               data = self.camera.capture_preview().get_data()
               return ByteArray(data)
            except piggyphoto.libgphoto2error as e:
                self.reset()

    def download_preview(self):
        if self._locked and self.do_preview:
            try:
                self.preview_lock = True
                self.camera.capture_preview('preview.jpg')
                self.preview_lock = False
                return True
            except piggyphoto.libgphoto2error as e:
                print e
                self.reset()

    def open_and_lock_camera(self):
        if self._locked:
            raise Exception
        self._locked = True
        self.camera = piggyphoto.camera()
        self.camera.leave_locked()
        g_camera = self.camera
        time.sleep(.5)

    def release_camera(self):
        self._locked = False
        self.camera = None

    def reset(self):
        self.release_camera()
        self.open_and_lock_camera()

service = PhotoboothService()
service.start_preview()


loop = gobject.MainLoop()

try:
    loop.run()
except:
    service.camera = None
    raise
