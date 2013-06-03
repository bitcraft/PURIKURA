#!/usr/bin/env python

import os
import glob
import pyrikura
import pygame

import kivy
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

DEFAULT_VKEYBOARD_LAYOUT = 'email'


os.chdir('/home/mjolnir/git/PURIKURA/')

# set keyboard behaviour to be a lit like ios
Config.set('kivy', 'keyboard_mode', 'dock')
Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)

# for the touch screen controller monitor
Config.set('graphics', 'fullscreen', True)
#Config.set('graphics', 'width', '1280')
#Config.set('graphics', 'height', '1024')

Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

Config.set('graphics', 'show_cursor', False)
Config.set('graphics', 'show_mousecursor', False)


thumbnails =  "/home/mjolnir/events/kali-joshua/small"
detail     =  "/home/mjolnir/events/kali-joshua/medium"
composites = '/home/mjolnir/events/gunnar-dolly/composites/'


class CompositePicker(pyrikura.kiosk.PickerScreen):
    def get_images(self):
        return glob.glob('{0}/*.png'.format(composites))


class Manager(ScreenManager):
    pass


class KioskApp(App):
    manager = Manager()

    def build(self):
        return self.manager


# disable the default mouse arrow cursor
cursor = pygame.cursors.load_xbm(
    os.path.join('images', 'hand.xbm'),
    os.path.join('images', 'hand-mask.xbm'))
pygame.mouse.set_cursor(*cursor)
pygame.mouse.set_visible(True)

app = KioskApp()
app.manager.add_widget(CompositePicker(name='compositepicker'))

app.run()

