from pyrikura.plugin import Plugin
from pyrikura.broker import Broker



class CTetherBroker(Broker):
    def process(self, msg, sender=None):
        self.publish([msg])

class CTether(Plugin):
    _decendant = CTetherBroker
