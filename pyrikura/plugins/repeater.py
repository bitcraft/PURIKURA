from pyrikura.plugin import Plugin
from pyrikura.broker import Broker
import time
import pygame
pygame.mixer.init()


# todo: handle midnight rollover

class CRepeaterBroker(Broker):
    def __init__(self, count, delay):
        super(CRepeaterBroker, self).__init__()
        self._busy = False
        self._msg = None
        self._last_publish = 0
        self._last_ding = 0
        self._current_count = 0
        self._count = count
        self._delay = delay
        self.sound = pygame.mixer.Sound('sounds/bell.wav')

    def process(self, msg, sender=None):
        if not self._busy:
            self._busy = True
            self._msg = msg
            self._last_publish = 0
            self._current_count = 0

    def update(self):
        if self._busy:
            now = time.time()
            if now - self._last_ding >= 1:
                self._last_ding = now
                self.sound.play()

            if now - self._last_publish >= self._delay:
                self.publish([self._msg])
                self._last_publish = now
                self._current_count += 1
                if self._current_count >= self._count:
                    self._busy = False

class CRepeater(Plugin):
    _decendant = CRepeaterBroker
