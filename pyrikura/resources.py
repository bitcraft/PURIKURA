__all__ = ('sounds', 'images', 'music', 'load', 'loaded')

from pyrikura.config import Config

import os
import pygame
import logging
logger = logging.getLogger('purikura.resources')

# because i am lazy
jpath = os.path.join

loaded = False
sounds = None
images = None
music = None


def load():
    global sounds, images, music, loaded

    if loaded:
        return

    sounds = dict()
    images = dict()
    music = dict()

    resource_path = Config.get('paths', 'resource-path')
    resource_path = os.path.abspath(resource_path)

    if Config.has_section('sound-files'):
        vol = Config.getint('sound', 'sound-volume') / 100.
        for name, filename in Config.items('sound-files'):
            path = jpath(resource_path, 'sounds', filename)
            logger.info("loading %s", path)
            sound = pygame.mixer.Sound(path)
            sound.set_volume(vol)
            sounds[name] = sound
            yield sound

    if Config.has_section('image-files'):
        for name, filename in Config.items('image-files'):
            path = jpath(resource_path, 'images', filename)
            logger.info("loading %s", path)
            #image = pygame.image.load(path)
            #images[name] = image
            #yield image

    if Config.has_section('music-files'):
        for name, filename in Config.items('music-files'):
            path = jpath(resource_path, 'music', filename)
            logger.info("loading %s", path)
            music[name] = path
            yield path

    loaded = True


def play_music(name):
    try:
        track = music[name]
        logger.info("playing %s", track)
        vol = Config.getint('sound', 'music-volume') / 100.
        if vol > 0:
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.load(track)
            pygame.mixer.music.play(-1)
    except pygame.error:
        pass
