
import os

os.chdir('/home/mjolnir/git/PURIKURA/')


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
#Config.set('graphics', 'width', '1280')
#Config.set('graphics', 'height', '1024')

Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

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
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.codeinput import CodeInput
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.screenmanager import SlideTransition, TransitionBase, WipeTransition

from kivy.loader import Loader
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.accordion import Accordion, AccordionItem

from kivy.properties import *

from kivy.factory import Factory


thumbnails =  "/home/mjolnir/events/kali-joshua/small"
detail     =  "/home/mjolnir/events/kali-joshua/medium"


large_preview_size = (1000,1000)


def handle_print_number_error(value):
    if value < 1:
        return 1
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



class IconAccordionItem(AccordionItem):
    icon_source = StringProperty()
    icon_size = ListProperty

    


class PickerScreen(Screen):

    def on_pre_enter(self):

        self.layout = search(self, 'layout')
        self.background = search(self, 'background')
        self.scrollview = search(self, 'scrollview')
        self.controls = search(self, 'controls')
        screen_width = int(Config.get('graphics', 'width'))
        screen_height = int(Config.get('graphics', 'height'))

        self.focus = None

        self.scrollview.bind(scroll_x=self.on_picker_scroll)
        self.scrollview.bind(pos=self.on_picker_move)

        self.background.y = -200

        images = get_images()
        width = math.ceil((len(images) / 2.0 * 312) / float(screen_width)) 
        self.max_width = int(width) * int(screen_width)

        # set the background to the correct position
        self.on_picker_scroll(None, None)

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


        # the center of the preview image
        center_x = screen_width - (large_preview_size[0] / 2) - 96

        self._focus_widget = Image(source='images/loading.gif')
        self._focus_widget.allow_stretch = True
        # defaults to the hidden state
        self._focus_widget.x = center_x - 500 + 450
        self._focus_widget.y = -1000
        self._focus_widget.size_hint = None, None
        self._focus_widget.size = (300, 300)
        self._focus_widget.bind(on_touch_down=self.on_image_touch)
        self.layout.add_widget(self._focus_widget)

        self.preview_label = Label(
            text='Touch preview to close',
            text_size=(500,100),
            font_size=30,
            pos=(-1000,-1000))

        self.layout.add_widget(self.preview_label)

    def hide_controls(self, widget, arg1):
        widget.pos_hint = {'x', 2} 
        return False

    def show_controls(self, widget, arg1):
        widget.pos_hint = {'x', 0} 
        return False

    def on_image_touch(self, widget, mouse_point):

        if widget.collide_point(mouse_point.x, mouse_point.y):
            screen_width = int(Config.get('graphics', 'width'))
            screen_height = int(Config.get('graphics', 'height'))
       
            # hide the focus widget
            if self.scrollview_hidden:
                self.scrollview_hidden = False
      
                # hide the controls
                ani = Animation(
                        opacity=0.0,
                        duration=.3)

                ani.bind(on_complete=self.hide_controls)
                ani.start(self.preview_label)
                ani.start(self.controls)

                # return the backdrop
                self.background_ani.stop(self.background)

                hw = screen_width / 2
                sp = self.max_width / float(6144)
                offset = (-self.scrollview.scroll_x * 6144 / sp) - hw
                ani = Animation(
                    y= self.background.y + 100, 
                    x = offset,
                    t='in_out_quad',
                    duration=.5)

                ani.start(self.background)

                
                # cancel scrollview hiding animation
                try:
                    self._sv_hide_ani.cancel(self.scrollview)
                except AttributeError:
                    pass

                # show the scrollview
                x, y = self._scrollview_pos
                self._sv_show_ani = Animation(
                    x=x,
                    y=y,
                    t='in_out_quad',
                    opacity=1.0,
                    duration=.5)

                self._sv_show_ani.start(self.scrollview)

                # cancel the focus widget show animation
                try:
                    self._focus_show_ani.cancel(self._focus_widget)
                except AttributeError:
                    pass

                screen_height = int(Config.get('graphics', 'height'))

                # hide the focus widget
                ani = Animation(
                    y=-1000,
                    x=self._focus_widget.x + 450,
                    size=(300,300),
                    t='in_out_quad',
                    duration=.5)

                ani &= Animation(
                    opacity=0.0,
                    duration=.5)
                
                ani.start(self._focus_widget)
                self._focus_hide_ani = ani

            # show the focus widget
            elif self._focus_widget is not widget:
                self.scrollview_hidden = True

                # show the controls
                ani = Animation(
                        opacity=1.0,
                        duration=.3)
        
                self.preview_label.pos_hint = {'x': .25, 'y': .47}
                self.controls.pos_hint = {'x': 0}
                self.controls.opacity = 0

                ani.start(self.preview_label)
                ani.start(self.controls)

                # cancel the scrollview show animation
                try:
                    self._sv_show_ani.cancel(self.scrollview)
                except AttributeError:
                    pass

                # hide the scrollview
                ani = Animation(
                    x=0,
                    y=-1000,
                    t='in_out_quad',
                    opacity=0.0,
                    duration=.7)

                ani.start(self.scrollview)
                self.sv_hide_ani = ani

                # make sure the focus animation is finished
                try:
                    self._focus_hide_ani.cancel(self._focus_widget)
                except AttributeError:
                    pass

                # set the focus widget to have the same image as the one picked
                # do a bit of mangling to get a more detailed image
                filename = os.path.join(detail, os.path.basename(widget.source))
                self._focus_widget.source = filename

                ani = Animation(
                    y= self.background.y - 100, 
                    x=-self.background.width/2.5,
                    t='in_out_quad',
                    duration=.5)

                ani += Animation(
                    x=0,
                    duration=480)

                ani.start(self.background)
                self.background_ani = ani

                # create animation to show the focus widget
                ani = Animation(
                    opacity=1.0,
                    y=50,
                    x=self._focus_widget.x - 450,
                    size=large_preview_size,
                    t='in_out_quad',
                    duration=.5)

                ani &= Animation(
                    opacity=1.0,
                    duration=.5)
            
                ani.start(self._focus_widget)
                self._focus_show_ani = ani

    def on_picker_move(self, widget, arg):
        return
        # this is the shift up/down animation
        if widget is self.scrollview:
            x, y = self.background.pos
            self.background.pos = (x, -arg[1] / 50)

    def on_picker_scroll(self, value1, value2):
        # this is the left/right parallax animation
        hw = 1920 / 2
        sp = self.max_width / float(6144)
        offset = (-self.scrollview.scroll_x * 6144 / sp) - hw
        self.background.pos = (offset, self.background.pos[1])
        return False

class StartScreen(Screen):
    pass

class SharingControls(FloatLayout):
    prints = BoundedNumericProperty(1, min=1, max=MAXIMUM_PRINTS,
        errorhandler = handle_print_number_error)

    twitter_acct = StringProperty('@kilbuckcreekphoto')

    _old_input_pos = None


    def check_email_focus(self, widget):
        return
        if widget.focus:
            self._old_input_pos = widget.pos
            ani = Animation(
                y=450,
                t='in_out_quad',
                duration = .3)
            ani.start(search(self, 'emailitem'))
        else:
            widget.pos = self._old_input_pos


    def add_print(self):
        self.prints += 1
        email_textinput = StringProperty()
        
    def remove_print(self):
        self.prints -= 1

    def spool_print(self):
        pass

    def change_vkeyboard_email(self):
        Config.set('kivy', 'keyboard_mode', 'dock')
        Config.set('kivy', 'keyboard_layout', 'email')

    def reset_email_textinput(self):
        self.email_textinput = ''
    
    def change_vkeyboard_normal(self):
        Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)


class PrintScreen(Screen):
    pass


class Manager(ScreenManager):
    def change_email(self):
        manager.transition = SlideTransition(duration=.75, direction='left')
        self.current = 'email'

    def change_picker(self):
        manager.transition = SlideTransition(duration=.75, direction='right')
        self.current = 'picker'


manager = Manager()
manager.add_widget(PickerScreen(name='picker'))
manager.add_widget(PrintScreen(name='print'))


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
    pygame.mouse.set_visible(True)

    app.run()

