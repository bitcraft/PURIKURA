from pyrikura.broker import Broker
from pyrikura.plugin import Plugin
import serial
import time


class ArduinoBroker(Broker):
    def __init__(self, *arg, **kwarg):
        super(ArduinoBroker, self).__init__(*arg, **kwarg)
        self._arg = arg
        self._kwarg = kwarg
        self.serial = None

    def open_arduino(self):
        self.serial = serial.Serial(*self._arg, timeout=1)
        self.clear()

    def close_arduino(self):
        self.serial = None

    def reset(self):
        self.close_arduino()
        self.open_arduino()

    def clear(self):
        while self.serial.read():
            pass

    def update(self, time=None):
        if self.serial:
            self.publish([self.serial.read(1)])
        else:
            self.reset()


class Arduino(Plugin):
    _decendant = ArduinoBroker
