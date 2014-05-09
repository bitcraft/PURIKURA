from pyrikura.broker import Broker
from pyrikura.plugin import Plugin
import pygame


pygame.mixer.init()


class CSoundBroker(Broker):
    def __init__(self, filename, trigger, *arg, **kwarg):
        super(CSoundBroker, self).__init__(*arg, **kwarg)
        self.sound = pygame.mixer.Sound(filename)
        self.trigger = trigger

    def process(self, msg, sender):
        self.sound.stop()
        self.sound.play()


class CSound(Plugin):
    _decendant = CSoundBroker
