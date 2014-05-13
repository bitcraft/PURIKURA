import time

from pyrikura.plugin import Plugin
from pyrikura.broker import Broker


class CRepeaterBroker(Broker):
    def __init__(self, count, delay=0, interval=0):
        super(CRepeaterBroker, self).__init__()
        self._busy = False
        self._msg = None
        self._last_publish = 0
        self._current_count = 0
        self._interval_count = 0
        self._count = count
        self._delay = delay
        self._interval = interval

    def process(self, msg, sender=None):
        if self._busy:
            self._interval_count += 1

        elif self._delay:
            self._last_publish = time.time()
            self._busy = True
            self._msg = msg
            self._current_count = 1
            self.publish([self._msg])

        elif self._interval:
            self._busy = True
            self._interval_count = 1

        if self._interval:
            if self._interval == self._interval_count:
                self.publish([self._msg])

            if self._interval_count == self._count * self._interval:
                self._busy = False

    def update(self):
        if self._busy and self._delay:
            if self._last_publish + self._delay <= time.time():
                self._last_publish = time.time()
                self._current_count += 1
                self.publish([self._msg])

                if self._current_count == self._count:
                    self._busy = False


class CRepeater(Plugin):
    _decendant = CRepeaterBroker
