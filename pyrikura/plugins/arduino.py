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
        self._locked = False

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
        self.unlock()

    def unlock(self):
        self._locked = False

    def lock(self):
        self._locked = True

    def update(self, time=None):
        if self._locked:
            return

        if self.serial:
            data = self.serial.readline()
            if data:
                self.publish(['capture.jpg'])
                self.lock()
        else:
            self.reset()

    def process(self, msg, sender=None):
        if self._locked:
            self.unlock()
            self.clear()


class Arduino(Plugin):
    _decendant = ArduinoBroker
