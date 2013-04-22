import kivy
kivy.require('1.5.0')

from kivy.config import Config

DEFAULT_VKEYBOARD_LAYOUT = 'qwerty'
DEFAULT_VKEYBOARD_LAYOUT = 'email'
MAXIMUM_PRINTS = 3

# set keyboard behaviour to be a lit like ios
Config.set('kivy', 'keyboard_mode', 'dock')
Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)

# for the touch screen controller monitor
Config.set('graphics', 'fullscreen', True)
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '1024')

# performance tweaks
Config.set('graphics', 'multisamples', 0)
#Config.set('graphics', 'maxfps', 40)

import os
import sys
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder, Parser, ParserException
from kivy.properties import *
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.codeinput import CodeInput
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.screenmanager import SlideTransition, TransitionBase

import pygame



def handle_print_number_error(value):
    if value < 0:
        return 0
    elif value > MAXIMUM_PRINTS:
        return MAXIMUM_PRINTS


Builder.load_file('kiosk.kv')


class StartScreen(Screen):
    pass

class EmailScreen(Screen):
    prints = BoundedNumericProperty(0, min=0, max=MAXIMUM_PRINTS,
        errorhandler = handle_print_number_error)

    def on_add_print(self):
        self.prints += 1

    def on_remove_print(self):
        self.prints -= 1

    def change_vkeyboard_email(self):
        Config.set('kivy', 'keyboard_mode', 'dock')
        Config.set('kivy', 'keyboard_layout', 'email')

    def change_vkeyboard_normal(self):
        Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)


class PrintScreen(Screen):
    pass


manager = ScreenManager()
manager.add_widget(StartScreen(name='start'))
manager.add_widget(EmailScreen(name='email'))
manager.add_widget(PrintScreen(name='print'))

# instant transition
manager.transition = TransitionBase(duration=0.01)

class KioskApp(App):
    def build(self):
        return manager


if __name__ == "__main__":
    # disable the default mouse arrow cursor

    pygame.init()
    cursor = pygame.cursors.load_xbm(
        os.path.join('images', 'hand.xbm'),
        os.path.join('images', 'hand-mask.xbm')
    )
    pygame.mouse.set_cursor(*cursor)

    app = KioskApp()
    app.run()

