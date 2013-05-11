from pyrikura.broker import Broker
from pyrikura.plugin import Plugin
import serial
import time



class ArduinoBroker(Broker):
    def __init__(self, *args, **kwargs):
        super(ArduinoBroker, self).__init__(*args, **kwargs)
        #self.serial = serial.Serial(*args, timeout=0)
        #time.sleep(2)
        #self.clear()
        pass

    def clear(self):
        while self.serial.read():
            pass


class ArduinoPlugin(Plugin):
    _decendant = ArduinoBroker


