from pyrikura.plugin import Plugin
from pyrikura.broker import Broker
import piggyphoto



class CTetherBroker(Broker):
    def __init__(self, name='capture.jpg'):
        super(CTetherBroker, self).__init__()
        #self.camera = piggyphoto.camera()
        #self.camera.leave_locked()
        self._name = name

    def process(self, msg, sender=None):
        #self.camera.capture_image(self._name)
        self.publish([self._name])

class CTether(Plugin):
    _decendant = CTetherBroker
