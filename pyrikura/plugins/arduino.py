from pyrikura.broker import Broker
from pyrikura.plugin import Plugin
import serial
import time



class ArduinoBroker(Broker):
    def __init__(self, *arg, **kwarg):
        super(ArduinoBroker, self).__init__(*arg, **kwarg)
        self.serial = serial.Serial(*arg, timeout=0)
        self.clear()

    def clear(self):
        while self.serial.read():
            pass


class Arduino(Plugin):
    _decendant = ArduinoBroker
