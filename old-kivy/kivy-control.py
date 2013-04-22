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

from kivy.graphics import Color, Rectangle

from kivy.lang import Builder


Builder.load_file('headnav.kv')

class HeadNav(BoxLayout):
    pass


def build_header(title):
    return HeadNav()


def build_toolbar(options):
    sizer = BoxLayout(oriention='horizontal', padding=5)

    for label, callback in options.items():
        button = Button(text=label)
        button.size_hint = (None, .5)
        sizer.add_widget(button)

    return sizer


options = {
    'camera': None,
    'processor': None,
}

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')

        header = build_header('Header')
        header.size_hint = 1, 1
        layout.add_widget(header)

        toolbar = build_toolbar(options)
        toolbar.size_hint = 1, .2
        #toolbar.pos_hint = {'top':1}
        layout.add_widget(toolbar)

        sizer1 = FloatLayout()
        s0 = Scatter(do_scale=False, do_rotation=False)
        s0.size_hint = (None, None)
        b1 = Label(text='New Sink')
        s0.add_widget(b1)
        sizer1.add_widget(s0)

        layout.add_widget(sizer1)

        return layout

if __name__ == '__main__':
    MyApp().run()
