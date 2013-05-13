from pyrikura.plugin import Plugin
from pyrikura.broker import Broker
import piggyphoto



class PPCameraBroker(Broker):
    def __init__(self):
        self.reset()

    def capture(self, filename=None):
        self.camera.capture_image(filename)

    def reset(self):
        self.camera = piggyphoto.camera()
        self.camera.leave_locked()

class PPCamera(Plugin):
    _decendant = PPCameraBroker
