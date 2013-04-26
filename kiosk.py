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
Config.set('graphics', 'show_cursor', False)
Config.set('graphics', 'show_mousecursor', False)

# performance tweaks
Config.set('graphics', 'multisamples', 0)

import os, sys, glob, math
from kivy.animation import Animation
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

from kivy.loader import Loader
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image

from kivy.factory import Factory


thumbnails =  "/home/mjolnir/events/kali-joshua/small"
detail     =  "/home/mjolnir/events/kali-joshua/medium"


def handle_print_number_error(value):
    if value < 0:
        return 0
    elif value > MAXIMUM_PRINTS:
        return MAXIMUM_PRINTS


def get_images():
    return glob.glob('{0}/*.JPG'.format(thumbnails))


Builder.load_file('kiosk.kv')

# hack search method because one is not included with kivy
def search(root, uniqueid):
    children = root.children[:]
    while children:
        child = children.pop()
        children.extend(child.children[:])

        try:
            child.uniqueid
        except:
            continue
        else:
            if child.uniqueid == uniqueid:
                return child

    return None

def show_cursor(widget, arg):
    pygame.mouse.set_visible(True)

def hide_cursor(widget, arg):
    pygame.mouse.set_visible(False)


class PickerScreen(Screen):
    def on_pre_enter(self):

        self.layout = search(self, 'layout')
        self.background = search(self, 'background')
        self.scrollview = search(self, 'scrollview')

        self.focus = None

        # set the background to the correct position
        self.on_picker_scroll(None, None)

        self.scrollview.bind(scroll_x=self.on_picker_scroll)
        self.scrollview.bind(pos=self.on_picker_move)

        images = get_images()
        width = math.ceil((len(images) / 2.0 * 312) / 1280.0) 
        self.max_width = width * 1280

        # set the width to be much great than the screen
        # somewhat proportionally to the number of images
        rellayout = search(self, 'rellayout')
        rellayout.size_hint = (width,1)

        grid = search(self, 'grid')

        Loader.loading_image = CoreImage('images/loading.gif')
        Loader.num_workers = 4
        Loader.max_upload_per_frame = 4

        for image in get_images():
            widget = Factory.AsyncImage(source=image, allow_stretch=True)
            widget.bind(on_touch_down=self.on_image_touch)
            grid.add_widget(widget)

        self.scrollview_hidden = False
        self._scrollview_pos_hint = self.scrollview.pos_hint
        self._scrollview_pos = self.scrollview.pos

        self._sv_hide_ani = None
        self._sv_show_ani = None

        self._focus_hide_ani = None
        self._focus_show_ani = None

        self._focus_widget = Image(source='images/loading.gif')
        self._focus_widget.allow_stretch = True
        self._focus_widget.pos_hint = {'center_x': .5}
        self._focus_widget.y = 1024
        self._focus_widget.size_hint = None, None
        self._focus_widget.size = (600, 600)
        self._focus_widget.bind(on_touch_down=self.on_image_touch)
        self.layout.add_widget(self._focus_widget)


    def on_image_touch(self, widget, mouse_point):
        if widget.collide_point(mouse_point.x, mouse_point.y):
        
            # show the focus widget
            if self.scrollview_hidden:
                self.scrollview_hidden = False
               
                # cancel scrollview hiding animation
                try:
                    self._sv_hide_ani.cancel(self.scrollview)
                except AttributeError:
                    pass

                # show the scrollview
                x, y = self._scrollview_pos
                self._sv_show_ani = Animation(x=x, y=y, t='in_out_quad', duration=.5)
                self._sv_show_ani.start(self.scrollview)

                # cancel the focus widget show animation
                try:
                    self._focus_show_ani.cancel(self._focus_widget)
                except AttributeError:
                    pass

                # hide the focus widget
                self._focus_hide_ani = Animation(y=1024,
                                                 size=(600,600),
                                                 t='in_out_quad',
                                                 duration=.5)

                self._focus_hide_ani.start(self._focus_widget)

            # hide the focus widget
            elif self._focus_widget is not widget:
                self.scrollview_hidden = True
              
                # cancel the scrollview show animation
                try:
                    self._sv_show_ani.cancel(self.scrollview)
                except AttributeError:
                    pass

                # hide the scrollview
                self.sv_hide_ani = Animation(x=0, y=-450, t='in_out_quad', duration=.5)
                self.sv_hide_ani.start(self.scrollview)

                # make sure the focus animation is finished
                try:
                    self._focus_hide_ani.cancel(self._focus_widget)
                except AttributeError:
                    pass

                # set the focus widget to have the same image as the one picked
                # do a bit of mangling to get a more detailed image
                filename = os.path.join(detail, os.path.basename(widget.source))
                self._focus_widget.source = filename

                # show the focus widget
                self._focus_show_ani = Animation(y=200,
                                                 size=(800, 800),
                                                 t='in_out_quad',
                                                 duration=.5)

                self._focus_show_ani.start(self._focus_widget)

    def on_picker_move(self, widget, arg):
        if widget is self.scrollview:
            x, y = self.background.pos
            self.background.pos = (x, -arg[1] / 50)

    def on_picker_scroll(self, value1, value2):
        self.background.pos = (self.scrollview.scroll_x*-600 - 100,
                               self.background.pos[1])
        return False


class StartScreen(Screen):
    pass

class EmailScreen(Screen):
    prints = BoundedNumericProperty(0, min=0, max=MAXIMUM_PRINTS,
        errorhandler = handle_print_number_error)

    def on_add_print(self):
        self.prints += 1

        email_textinput = StringProperty()
        
    def remove_print(self):
        self.prints -= 1

    def change_vkeyboard_email(self):
        Config.set('kivy', 'keyboard_mode', 'dock')
        Config.set('kivy', 'keyboard_layout', 'email')

    def reset_email_textinput(self):
        self.email_textinput = ''
    
    def change_vkeyboard_normal(self):
        Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)


class PrintScreen(Screen):
    pass

manager = ScreenManager()
manager.add_widget(PickerScreen(name='picker'))
manager.add_widget(StartScreen(name='start'))
manager.add_widget(EmailScreen(name='email'))
manager.add_widget(PrintScreen(name='print'))

# instant transition
manager.transition = TransitionBase(duration=0.01)

class KioskApp(App):
    def build(self):
        return manager


if __name__ == "__main__":
    import pygame

    app = KioskApp()

    # disable the default mouse arrow cursor
    cursor = pygame.cursors.load_xbm(
        os.path.join('images', 'hand.xbm'),
        os.path.join('images', 'hand-mask.xbm')
    )
    pygame.mouse.set_cursor(*cursor)
    #pygame.mouse.set_visible(False)

    app.run()

