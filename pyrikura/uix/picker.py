from kivy.config import Config
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.image import ImageData
from kivy.graphics.texture import Texture
from kivy.factory import Factory
from kivy.factory import Factory
from kivy.loader import Loader
from kivy.properties import *

from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider

from six.moves import cStringIO, queue
import PIL
import PIL.Image
import os
import pygame
import threading
import time
import dbus
import logging

from ..config import Config as pkConfig
from .sharing import SharingControls

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('purikura.picker')

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


class PreviewGetThread(threading.Thread):
    """ Pulls data from dbus service and prepares it for the preview widget
    """
    def __init__(self, q):
        super(PreviewGetThread, self).__init__()
        bus = dbus.SessionBus()
        pb_obj = bus.get_object(dbus_name, dbus_path)
        self.iface = dbus.Interface(pb_obj, dbus_interface=dbus_name)
        self.iface.open_camera()
        self.queue = q
        self.daemon = True
        self._running = False

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        interval = pkConfig.getfloat('camera', 'preview-interval')
        download_preview = self.iface.download_preview
        queue_put = self.queue.put
        pil_open = PIL.Image.open

        while self._running:
            time.sleep(interval)
            result, data = download_preview(byte_arrays=True)

            if result:
                im = pil_open(cStringIO(str(data)))
                im = im.transpose(PIL.Image.FLIP_TOP_BOTTOM)
                imdata = ImageData(im.size[0],
                                   im.size[1],
                                   im.mode.lower(),
                                   im.tostring())
                queue_put(imdata)


class PreviewHandler(object):
    """ Manages the PreviewThread
    """
    def __init__(self, q):
        self.thread = None
        self.queue = q

    def start(self):
        if self.thread is None:
            logger.debug('starting the preview handler')
            self.thread = PreviewGetThread(self.queue)
            self.thread.start()
        else:
            logger.debug('want to start preview thread, but already running')

    def stop(self):
        if self.thread is None:
            logger.debug('want to stop preview thread, but is not running')
        else:
            logger.debug('stopping the preview handler')
            self.thread.stop()
            self.thread = None


class ArduinoHandler(object):
    """ Manages connections to the arduino to send camera tilt information
    """
    def __init__(self):
        bus = dbus.SessionBus()
        pb_obj = bus.get_object(dbus_name, dbus_path)
        self.iface = dbus.Interface(pb_obj, dbus_interface=dbus_name)
        self.iface.open_arduino()

    def set_camera_tilt(self, value):
        try:
            value = int(value)
        except ValueError:
            logger.debug('cannot accept %s for camera tilt', value)
            return

        self.iface.set_camera_tilt(value)


class PickerScreen(Screen):
    """ A nice looking touch-enabled file browser

    state transistions need some work...a lot of work.
    """
    large_preview_size = ListProperty()
    small_preview_size = ListProperty()
    grid_rows = NumericProperty()
    images = ListProperty()

    def __init__(self, *args, **kwargs):
        super(PickerScreen, self).__init__(*args, **kwargs)

        # these declarations are mainly to keep pycharm from annoying me with
        # notification that these attributes are not declared in __init__
        self.arduino_handler = None
        self.preview_handler = None
        self.preview_queue = None
        self.preview_widget = None
        self.preview_label = None
        self.preview_exit = None
        self.focus_widget = None
        self.layout = None
        self.background = None
        self.scrollview = None
        self.grid = None
        self.locked = None
        self.loaded = None
        self.state = 'normal'

    def on_pre_enter(self):
        # set up the 'normal' state

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
        Loader.num_workers = pkConfig.getint('kiosk', 'loaders')
        Loader.max_upload_per_frame = pkConfig.getint('kiosk',
                                                      'max-upload-per-frame')

        self.scrollview_hidden = False
        self._scrollview_pos_hint = self.scrollview.pos_hint
        self._scrollview_pos = self.scrollview.pos

        # the center of the preview image
        center_x = screen_width - (self.large_preview_size[0] / 2) - 16

        # stuff for the arduino/tilt
        self.arduino_handler = ArduinoHandler()
        def set_camera_tilt(widget, value):
            self.arduino_handler.set_camera_tilt(value)

        #   F O C U S   W I D G E T
        # the focus widget is the large preview image
        self.focus_widget = Image(source=image_path('loading.gif'))
        self.focus_widget.allow_stretch = True
        self.focus_widget.x = center_x - OFFSET
        self.focus_widget.y = -1000
        self.focus_widget.size_hint = None, None
        self.focus_widget.size = self.small_preview_size
        self.focus_widget.bind(on_touch_down=self.on_image_touch)
        self.layout.add_widget(self.focus_widget)

        # this handles pulling the preview images from the dbus service
        # queueing them and updaing the widget's texture
        self.preview_queue = queue.Queue()
        self.preview_handler = PreviewHandler(self.preview_queue)
        self.preview_handler.start()
        self.preview_widget = None   # will be created on first image

        #   P R E V I E W   W I D G E T
        # handles updating the widget.  pygame doesn't allow creating surfaces
        # in the main thread, so it must be done here.
        # in the future, using another library, such as pil, may allow
        # offloading the image loading into another thread
        def update_preview(*args, **kwargs):
            try:
                imdata = self.preview_queue.get(False)
            except queue.Empty:
                return

            # textures must be created in the main thread (pygame)
            texture = Texture.create_from_data(imdata)

            if self.preview_widget is None:
                max = pkConfig.getint('arduino', 'max-tilt')
                min = pkConfig.getint('arduino', 'min-tilt')

                def on_move(widget, touch):
                    print touch

                self.preview_widget = Image(texture=texture, nocache=True)
                self.preview_widget.allow_stretch = True
                self.preview_widget.size_hint = None, None
                self.preview_widget.size = (1280, 1024)
                self.preview_widget.x = 0
                self.preview_widget.y = self.preview_widget.height
                self.preview_widget.bind(on_move=on_move)
                self.layout.add_widget(self.preview_widget)
            else:
                self.preview_widget.texture = texture

        #   E X I T   B U T T O N
        # this button is used to exit the large camera preview window
        self.preview_exit = Image(source=image_path('chevron-right.gif'))
        self.preview_exit.allow_stretch = True
        self.preview_exit.keep_ratio = False
        self.preview_exit.size_hint = None, None
        self.preview_exit.width = 64
        self.preview_exit.height = 175
        self.preview_exit.x = 1280
        self.preview_exit.y = (1024 / 2) - (self.preview_exit.height / 2)
        self.layout.add_widget(self.preview_exit)

        #   P R E V I E W   L A B E L
        # the preview label is used with the focus widget is open
        self.preview_label = Label(
            text='Touch preview to close',
            text_size=(500, 100),
            font_size=30,
            pos=(-1000, -1000))
        self.layout.add_widget(self.preview_label)

        # the scrollview is amimated to move in and out
        self.scrollview.original_y = 100
        self.scrollview.y = self.scrollview.original_y
        self.scrollview.bind(scroll_x=self.on_picker_scroll)

        # the background has a parallax effect, so position is manually now
        self.background.y = -400
        self.background.pos = self._calc_bg_pos()

        # locked and loaded  =D
        self.locked = False
        self.loaded = set()

        # schedule an interval to update the preview widget
        Clock.schedule_interval(update_preview,
                                pkConfig.getfloat('camera', 'preview-interval'))

        # schedule a callback to check for new images
        Clock.schedule_interval(self.scan, 1)

    def scan(self, dt):
        """ Scan for new images and scroll to edge if found
        """
        new = False
        for filename in self.get_images():
            if filename not in self.loaded:
                new = True
                self.loaded.add(filename)
                widget = self._create_preview_widget(filename)
                self.grid.add_widget(widget)

        # move and animate the scrollview to the far edge
        if new:
            ani = Animation(
                scroll_x=.99,
                t='in_out_quad',
                duration=1)

            ani.start(self.scrollview)

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

    def change_state(self, state, **kwargs):
        screen_width = int(Config.get('graphics', 'width'))
        screen_height = int(Config.get('graphics', 'height'))

        transition = None

        new_state = state
        old_state = self.state
        self.state = new_state
        transition = (old_state, self.state)

        #====================================================================
        #  F O C U S  =>  N O R M A L
        if transition == ('focus', 'normal'):
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

        #=====================================================================
        #  N O R M A L  =>  F O C U S
        elif transition == ('normal', 'focus'):
            widget = kwargs['widget']

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
                x=(1280 / 2) - 250,
                size=self.large_preview_size,
                t='in_out_quad',
                duration=.5)

            ani &= Animation(
                opacity=1.0,
                duration=.5)

            ani.start(self.focus_widget)

        #=====================================================================
        #  N O R M A L  =>  P R E V I E W
        elif transition == ('normal', 'preview'):
            pass

        #=====================================================================
        #  P R E V I E W  =>  N O R M A L
        elif transition == ('preview', 'normal'):
            pass

    def on_image_touch(self, widget, mouse_point):
        """ called when any image is touched
        """
        if self.locked:
            return

        if widget.collide_point(mouse_point.x, mouse_point.y):
            # hide the focus widget
            if self.scrollview_hidden:
                self.change_state('normal', widget=widget)

            # show the focus widget
            elif self.focus_widget is not widget:
                if widget is self.preview_widget:
                    return False

                self.change_state('focus', widget=widget)

    def on_picker_scroll(self, *arg):
        # this is the left/right parallax animation
        if not self.locked:
            self.background.pos = self._calc_bg_pos()
        return True

    def _calc_bg_pos(self):
        bkg_w = self.background.width * .3
        return (-self.scrollview.scroll_x * bkg_w - self.width / 2,
                self.background.pos[1])
