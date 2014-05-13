#!/usr/bin/env python
"""
Operator's kiosk for managing the photobooth
"""
import os
import glob
import logging

import pygame

from pyrikura import kiosk
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager


DEFAULT_VKEYBOARD_LAYOUT = 'email'

logger = logging.getLogger("purikura.main")


# set keyboard behaviour to be a little like ios
Config.set('kivy', 'keyboard_mode', 'dock')
Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)

Config.set('graphics', 'fullscreen', True)
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '1024')

event = 'test'
root = '/home/mjolnir/events/{}'.format(event)
thumbnails = '{}/small'.format(root)
detail = '{}/medium'.format(root)
originals = '{}/originals'.format(root)
composites = '{}/composites/'.format(root)

# make sure directory structure is usuable
for d in (root, thumbnails, detail, originals, composites):
    try:
        isdir = os.path.isdir(d)
    except:
        raise

    if not isdir:
        os.makedirs(d, 0755)

module = 'pyrikura'
Builder.load_file(os.path.join(module, 'kiosk-composite.kv'))


class CompositePicker(kiosk.PickerScreen):
    """
    Image browser that displays composites
    """

    def get_paths(self):
        return composites, composites, composites, composites

    def get_images(self):
        return sorted(glob.glob('{0}/*.png'.format(composites)))


class SinglePicker(kiosk.PickerScreen):
    """
    Image browser that uses displays one image at a time
    """

    def get_paths(self):
        return thumbnails, detail, originals, composites

    def get_images(self):
        return sorted(glob.glob('{0}/*.jpg'.format(thumbnails)))


class Manager(ScreenManager):
    pass


class KioskApp(App):
    manager = Manager()

    def build(self):
        return self.manager


if __name__ == '__main__':
    cursor = pygame.cursors.load_xbm(
        os.path.join('resources/../resources/images', 'blank-cursor.xbm'),
        os.path.join('resources/../resources/images', 'blank-cursor-mask.xbm'))
    pygame.mouse.set_cursor(*cursor)

    app = KioskApp()
    #app.manager.add_widget(SinglePicker(name='singlepicker'))
    app.manager.add_widget(CompositePicker(name='compositepicker'))

    app.run()

