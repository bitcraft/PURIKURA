import kivy
kivy.require('1.5.1') # replace with your current kivy version !

from kivy.app import App

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.layout import Layout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.screenmanager import SlideTransition, TransitionBase

from kivy.graphics import Color, Rectangle

from kivy.lang import Builder

Builder.load_file('kiosk.kv')


class StartScreen(Screen):
    pass

class EmailScreen(Screen):
    pass

class PrintScreen(Screen):
    pass


manager = ScreenManager()
manager.add_widget(StartScreen(name='start'))
manager.add_widget(EmailScreen(name='email'))
manager.add_widget(PrintScreen(name='print'))

# instant transition
manager.transition = TransitionBase(duration=0.01)

class kioskApp(App):
    def build(self):
        return manager

if __name__ == '__main__':
    kioskApp().run()
