#!/usr/bin/env pytghthon
"""
Operator's kiosk for managing the photobooth
"""
import sys
sys.path.append('/home/mjolnir/git/PURIKURA/')

import os
import glob
import logging
import pygame
import ConfigParser
import pyrikura
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager


DEFAULT_VKEYBOARD_LAYOUT = 'email'

logger = logging.getLogger("purikura.kiosk-loader")

# because i hate typing
jpath = os.path.join


def load_config(name):
    path = jpath('/home/mjolnir/git/PURIKURA/config', name)
    cfg = ConfigParser.ConfigParser()
    msg = 'loading kiosk configuration from {}...'
    logger.info(msg.format(path))
    cfg.read(path)
    return cfg

cfg = load_config('kiosk.ini')


# set keyboard behaviour to be a little like ios
Config.set('kivy', 'keyboard_mode', 'dock')
Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)

# set the display up
Config.set('graphics', 'fullscreen', cfg.getboolean('display', 'fullscreen'))
Config.set('graphics', 'width', cfg.getint('display', 'width'))
Config.set('graphics', 'height', cfg.getint('display', 'height'))

# the display/touch input i use needs some love
Config.set('postproc', 'retain_time', 170)
Config.set('postproc', 'retain_distance', 90)

# load the config from the service to get path info
# this is mostly copypasta from service.py
cfg = load_config('service.ini')

# paths
app_root_path = cfg.get('paths', 'root')
app_config_path = jpath(app_root_path, 'config')
app_resources_path = jpath(app_root_path, 'resources')
app_sounds_path = jpath(app_resources_path, 'sounds')
app_images_path = jpath(app_resources_path, 'images')
all_templates_path = jpath(app_resources_path, 'templates')
all_images_path = cfg.get('paths', 'images')
capture_image = cfg.get('camera', 'capture-image')
shared_path = cfg.get('paths', 'shared')
plugins_path = cfg.get('paths', 'plugins')

# event paths
event_name = cfg.get('event', 'name')
template_path = jpath(all_templates_path, cfg.get('event', 'template'))
event_images_path = jpath(all_images_path, event_name)
thumbs_path = jpath(event_images_path, 'thumbnails')
details_path = jpath(event_images_path, 'detail')
originals_path = jpath(event_images_path, 'originals')
composites_path = jpath(event_images_path, 'composites')
paths = ('thumbnails', 'detail', 'originals', 'composites')


# make sure directory structure is usuable
for d in (thumbs_path, details_path, originals_path, composites_path):
    try:
        isdir = os.path.isdir(d)
    except:
        raise

    if not isdir:
        os.makedirs(d, 0755)

module = 'pyrikura'
Builder.load_file(os.path.join(module, 'kiosk-composite.kv'))


class CompositePicker(pyrikura.kiosk.PickerScreen):
    """
    Image browser that displays composites
    """
    @staticmethod
    def get_paths():
        return composites_path, composites_path,\
               composites_path, composites_path

    @staticmethod
    def get_images():
        return sorted(glob.glob('{0}/*.png'.format(composites_path)))


class SinglePicker(pyrikura.kiosk.PickerScreen):
    """
    Image browser that uses displays one image at a time
    """
    @staticmethod
    def get_paths():
        return thumbs_path, details_path, originals_path, composites_path

    @staticmethod
    def get_images():
        return sorted(glob.glob('{0}/*.jpg'.format(thumbs_path)))


class Manager(ScreenManager):
    pass


class KioskApp(App):
    manager = Manager()

    def build(self):
        return self.manager


if __name__ == '__main__':
    cursor = pygame.cursors.load_xbm(
        os.path.join(app_images_path, 'blank-cursor.xbm'),
        os.path.join(app_images_path, 'blank-cursor-mask.xbm'))
    pygame.mouse.set_cursor(*cursor)

    app = KioskApp()
    #app.manager.add_widget(SinglePicker(name='singlepicker'))
    app.manager.add_widget(CompositePicker(name='compositepicker'))

    app.run()

