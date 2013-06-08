from pyrikura.plugin import Plugin
from pyrikura.broker import Broker
import piggyphoto
import time



class CTetherBroker(Broker):
    def __init__(self, name='capture.jpg', test=False):
        super(CTetherBroker, self).__init__()
        self._name = name
        self._test = test
        self._locked = True
        self.camera = None
        self.reset()

    def process(self, msg, sender=None):
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

class CTether(Plugin):
    _decendant = CTetherBroker
