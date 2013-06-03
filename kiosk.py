#!/usr/bin/env python

import os
import glob
import pygame
import pyrikura

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
#Config.set('graphics', 'width', '1280')
#Config.set('graphics', 'height', '1024')

Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

#Config.set('graphics', 'show_cursor', False)
#Config.set('graphics', 'show_mousecursor', False)


thumbnails =  "/home/mjolnir/events/kali-joshua/small"
detail     =  "/home/mjolnir/events/kali-joshua/medium"
composites = '/home/mjolnir/events/gunnar-dolly/composites/'



class CompositePicker(pyrikura.kiosk.PickerScreen):
    def get_images(self):
        return sorted(glob.glob('{0}/*.png'.format(composites)))


class SinglePicker(pyrikura.kiosk.PickerScreen):
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
        os.path.join('images', 'hand.xbm'),
        os.path.join('images', 'hand-mask.xbm'))
    pygame.mouse.set_cursor(*cursor)

    app = KioskApp()
    app.manager.add_widget(SinglePicker(name='singlepicker'))
    app.manager.add_widget(CompositePicker(name='compositepicker'))

    app.run()

