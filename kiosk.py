#!/usr/bin/env python

import os
import glob
import pygame
from pyrikura import kiosk

import kivy
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

DEFAULT_VKEYBOARD_LAYOUT = 'email'

# set keyboard behaviour to be a little like ios
Config.set('kivy', 'keyboard_mode', 'dock')
Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)

Config.set('graphics', 'fullscreen', True)
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '1024')


event = 'test'
thumbnails = '/home/mjolnir/events/{}/small'.format(event)
detail     = '/home/mjolnir/events/{}/medium'.format(event)
originals  = '/home/mjolnir/events/{}/originals'.format(event)
composites = '/home/mjolnir/events/{}/composites/'.format(event)

module = 'pyrikura'
Builder.load_file(os.path.join(module, 'kiosk-composite.kv'))

class CompositePicker(kiosk.PickerScreen):
    def get_paths(self):
        return composites, composites, composites, composites

    def get_images(self):
        return sorted(glob.glob('{0}/*.png'.format(composites)))


class SinglePicker(kiosk.PickerScreen):
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
        os.path.join('images', 'blank-cursor.xbm'),
        os.path.join('images', 'blank-cursor-mask.xbm'))
    #pygame.mouse.set_cursor(*cursor)

    app = KioskApp()
    #app.manager.add_widget(SinglePicker(name='singlepicker'))
    app.manager.add_widget(CompositePicker(name='compositepicker'))

    app.run()

