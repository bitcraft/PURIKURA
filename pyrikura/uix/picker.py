from kivy.animation import Animation
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.image import Image as CoreImage
from kivy.core.image import ImageData
from kivy.factory import Factory
from kivy.factory import Factory
from kivy.loader import Loader
from kivy.properties import *

from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider

from six.moves import cStringIO
import shutter
import pygame
import threading

from ..config import Config as pkConfig
from .sharing import SharingControls


camera = shutter.Camera()
serial_lock = threading.Lock()

import os

OFFSET = 172
dbus_name = pkConfig.get('camera', 'dbus-name')
dbus_path = pkConfig.get('camera', 'dbus-path')
jpath = os.path.join


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


def image_path(filename):
    return jpath('/home/mjolnir/git/PURIKURA/resources/images/', filename)


class PickerScreen(Screen):
    large_preview_size = ListProperty()
    small_preview_size = ListProperty()
    grid_rows = NumericProperty()
    images = ListProperty()

    def on_pre_enter(self):

        # schedule a callback to check for new images
        Clock.schedule_interval(self.scan, 1)

        self.layout = search(self, 'layout')
        self.background = search(self, 'background')
        self.scrollview = search(self, 'scrollview')
        self.grid = search(self, 'grid')

        screen_width = int(Config.get('graphics', 'width'))
        screen_height = int(Config.get('graphics', 'height'))

        # the grid will expand horizontally as items are added
        self.grid.bind(minimum_width=self.grid.setter('width'))

        # tweak the loading so it is quick
        Loader.loading_image = CoreImage(image_path('loading.gif'))
        Loader.num_workers = 6
        Loader.max_upload_per_frame = 5

        self.scrollview_hidden = False
        self._scrollview_pos_hint = self.scrollview.pos_hint
        self._scrollview_pos = self.scrollview.pos

        # the center of the preview image
        center_x = screen_width - (self.large_preview_size[0] / 2) - 16

        import serial
        arduino = serial.Serial(pkConfig.get('arduino', 'port'),
                                pkConfig.getint('arduino', 'baudrate'))

        def on_tilt(widget, value):
            print value
            arduino.write(chr(0x80))
            arduino.write(chr(int(value)))
            arduino.flush()

        self.tilt_slider = Slider(min=pkConfig.getint('arduino', 'max-tilt'),
                                  max=pkConfig.getint('arduino', 'min-tilt'),
                                  value=pkConfig.getint('arduino', 'tilt'),
                                  orientation='vertical')

        self.layout.add_widget(self.tilt_slider)

        self.tilt_slider.bind(value=on_tilt)

        # defaults to the hidden state
        self.focus_widget = Image(source=image_path('loading.gif'))
        self.focus_widget.allow_stretch = True
        self.focus_widget.x = center_x - OFFSET
        self.focus_widget.y = -1000
        self.focus_widget.size_hint = None, None
        self.focus_widget.size = self.small_preview_size
        self.focus_widget.bind(on_touch_down=self.on_image_touch)
        self.layout.add_widget(self.focus_widget)

        self.preview_widget = None

        def touch_preview(widget, mouse_point):
            if widget.collide_point(mouse_point.x, mouse_point.y):
                #pb_iface.capture_preview()
                if os.path.exists('preview.jpg'):
                    widget.source = 'preview.jpg'
                    widget.reload()

        def update_preview(*args, **kwargs):
            filename = 'preview.jpg'
            fmt = 'rgb'
            im = pygame.image.load(
                cStringIO(
                    camera.capture_preview().get_data()
                )
            ).convert()
            data = pygame.image.tostring(im, fmt.upper())
            imgdata = ImageData(im.get_width(), im.get_height(), fmt, data)

            if self.preview_widget is None:
                self.preview_widget = Image(image=imgdata, nocache=True)
                self.preview_widget.allow_stretch = True
                self.preview_widget.x = center_x - OFFSET
                self.preview_widget.y = 0
                self.preview_widget.size_hint = None, None
                self.preview_widget.size = (200, 200)
                self.preview_widget.bind(on_touch_down=self.on_image_touch)
                self.layout.add_widget(self.preview_widget)
            else:
                self.preview_widget.image = imgdata
                #self.preview_widget.reload()
            print 'update'

        Clock.schedule_interval(update_preview, .5)

        #pb_iface.connect_to_signal('preview_updated', touch_preview)

        self.preview_label = Label(
            text='Touch preview to close',
            text_size=(500, 100),
            font_size=30,
            pos=(-1000, -1000))
        self.layout.add_widget(self.preview_label)

        self.scrollview.original_y = 100
        self.scrollview.y = self.scrollview.original_y
        self.scrollview.bind(scroll_x=self.on_picker_scroll)

        # the background has a parallax effect, so position is manually now
        self.background.y = -400
        self.background.pos = self._calc_bg_pos()

        self.locked = False
        self.loaded = set()

    def scan(self, dt):

        # load images from disk
        for filename in self.get_images():
            if filename not in self.loaded:
                self.loaded.add(filename)
                widget = self._create_preview_widget(filename)
                self.grid.add_widget(widget)
                if not self.scrollview_hidden:
                    self.background.pos = self._calc_bg_pos()

    def _create_preview_widget(self, source):
        widget = Factory.AsyncImage(
            source=source,
            allow_stretch=True,
            pos_hint={'top': 1})
        widget.bind(on_touch_down=self.on_image_touch)
        return widget

    def _remove_widget_after_ani(self, ani, widget):
        self.remove_widget(widget)

    def show_controls(self, widget, arg):
        widget.pos_hint = {'x', 0}
        return False

    def unlock(self, dt=None):
        self.locked = False

    def on_image_touch(self, widget, mouse_point):
        if self.locked:
            return

        if widget.collide_point(mouse_point.x, mouse_point.y):
            screen_width = int(Config.get('graphics', 'width'))
            screen_height = int(Config.get('graphics', 'height'))

            # hide the focus widget
            if self.scrollview_hidden:
                self.scrollview_hidden = False
                self.locked = True

                # schedule a unlock
                Clock.schedule_once(self.unlock, .5)

                # cancel all running animation
                Animation.cancel_all(self.controls)
                Animation.cancel_all(self.scrollview)
                Animation.cancel_all(self.background)
                Animation.cancel_all(self.focus_widget)

                # close the keyboard
                from kivy.core.window import Window

                Window.release_all_keyboards()

                # disable the controls (workaround until 1.8.0)
                self.controls.disable()

                # hide the controls
                ani = Animation(
                    opacity=0.0,
                    duration=.3)

                ani.bind(on_complete=self._remove_widget_after_ani)
                ani.start(self.preview_label)
                ani.start(self.controls)

                # set the background to normal
                x, y = self._calc_bg_pos()
                ani = Animation(
                    y=y + 100,
                    x=x,
                    t='in_out_quad',
                    duration=.5)

                ani.start(self.background)

                # show the scrollview
                x, y = self._scrollview_pos[0], self.scrollview.original_y
                ani = Animation(
                    x=x,
                    y=y,
                    t='in_out_quad',
                    opacity=1.0,
                    duration=.5)

                ani.start(self.scrollview)

                # hide the focus widget
                ani = Animation(
                    y=-1000,
                    x=self.focus_widget.x + OFFSET,
                    size=self.small_preview_size,
                    t='in_out_quad',
                    duration=.5)

                ani &= Animation(
                    opacity=0.0,
                    duration=.5)

                ani.start(self.focus_widget)

            # show the focus widget
            elif self.focus_widget is not widget:
                if widget is self.preview_widget:
                    return False

                self.scrollview_hidden = True
                self.locked = True

                # schedule a unlock
                Clock.schedule_once(self.unlock, .5)

                # cancel all running animation
                Animation.cancel_all(self.scrollview)
                Animation.cancel_all(self.background)
                Animation.cancel_all(self.focus_widget)

                # set the focus widget to have the same image as the one picked
                # do a bit of mangling to get a more detailed image
                thumb, detail, original, comp = self.get_paths()
                filename = os.path.join(detail, os.path.basename(widget.source))
                original = os.path.join(original,
                                        os.path.basename(widget.source))

                # get a medium resolution image for the preview
                self.focus_widget.source = filename

                # show the controls
                self.controls = SharingControls()
                self.controls.filename = original
                self.controls.size_hint = .40, 1
                self.controls.opacity = 0

                ani = Animation(
                    opacity=1.0,
                    duration=.3)

                self.preview_label.pos_hint = {'x': .25, 'y': .47}

                ani.start(self.preview_label)
                ani.start(self.controls)

                # set the z to something high to ensure it is on top
                self.add_widget(self.controls)

                # hide the scrollview
                ani = Animation(
                    x=0,
                    y=-1000,
                    t='in_out_quad',
                    opacity=0.0,
                    duration=.7)

                ani.start(self.scrollview)

                # start a simple animation on the background
                ani = Animation(
                    y=self.background.y - 100,
                    x=-self.background.width / 2.5,
                    t='in_out_quad',
                    duration=.5)

                ani += Animation(
                    x=0,
                    duration=480)

                ani.start(self.background)

                hh = (screen_height - self.large_preview_size[1]) / 2
                # show the focus widget
                ani = Animation(
                    opacity=1.0,
                    y=screen_height - self.large_preview_size[1] - hh,
                    x=self.focus_widget.x - OFFSET,
                    size=self.large_preview_size,
                    t='in_out_quad',
                    duration=.5)

                ani &= Animation(
                    opacity=1.0,
                    duration=.5)

                ani.start(self.focus_widget)

    def on_picker_scroll(self, *arg):
        # this is the left/right parallax animation
        if not self.locked:
            self.background.pos = self._calc_bg_pos()

    def _calc_bg_pos(self):
        bkg_w = self.background.width * .3

        return (-self.scrollview.scroll_x * bkg_w - self.width / 2,
                self.background.pos[1])


def send_to_serial(value):
    pass