from pyrikura.plugin import Plugin
from pyrikura.broker import Broker
import dbus



class CTetherBroker(Broker):
    def __init__(self, filename='capture.jpg', test=False):
        super(CTetherBroker, self).__init__()
        self._filename = filename

        bus = dbus.SessionBus()
        pb_obj = bus.get_object('com.kilbuckcreek.photobooth',
                                '/com/kilbuckcreek/photobooth')

        self.pb_iface = dbus.Interface(pb_obj,
            dbus_interface='com.kilbuckcreek.photobooth')


    def process(self, msg, sender=None):
        result = self.pb_iface.test()
        if result:
            self.publish([self._filename])
        else:
            self.error()

class CTether(Plugin):
    _decendant = CTetherBroker
