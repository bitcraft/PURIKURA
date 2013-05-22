from pyrikura.broker import Broker
from pyrikura.plugin import Plugin
import serial
import time



class ArduinoBroker(Broker):
    def __init__(self, *arg, **kwarg):
        super(ArduinoBroker, self).__init__(*arg, **kwarg)
        self.serial = serial.Serial(*arg, timeout=1)
        self.clear()

    def clear(self):
        while self.serial.read():
            pass

    def update(self, time=None):
        i = self.serial.read(1)
        if i:
            print i
            self.publish(['capture.jpg'])
            self.clear()

class Arduino(Plugin):
    _decendant = ArduinoBroker
