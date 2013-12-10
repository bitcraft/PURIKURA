import dbus
import gobject
import piggyphoto
from dbus.service import Object
from dbus.mainloop.glib import DBusGMainLoop



DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()


class PhotoboothService(dbus.service.Object):
    def __init__(self):
        name = dbus.service.BusName('com.kilbuckcreek.photobooth', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, name, '/com/kilbuckcreek/photobooth')
        self._name = name
        self._test = test
        self._locked = True
        self.camera = None
        self.reset()

    @dbus.service.method('com.kilbuckcreek.photobooth')
    def test(self):
        print "trying..."
        if self._locked:
            try:
                self.camera.capture_image(self._name)
            except piggyphoto.libgphoto2error:
                self.reset()
                self.camera.capture_image(self._name)

            self.publish([self._name])

        elif self._test:
            self.publish([self._name])
        return 'hello!'

    def open_and_lock_camera(self):
        if self._locked:
            raise Exception
        self._locked = True
        self.camera = piggyphoto.camera()
        self.camera.leave_locked()
        time.sleep(.5)

    def release_camera(self):
        self._locked = False
        self.camera = None

    def reset(self):
        if not self._test:
            self.release_camera()
            self.open_and_lock_camera()

service = PhotoboothService()

o = bus.get_object("com.kilbuckcreek.photobooth", "/com/kilbuckcreek/photobooth")

loop = gobject.MainLoop()
loop.run()
