#!/usr/bin/env python

import kivy
kivy.require('1.8.0')

import dbus
import os
import shutil
from functools import partial
from dbus.mainloop.glib import DBusGMainLoop

from . import config

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.image import Image as CoreImage
from kivy.factory import Factory
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.loader import Loader
from kivy.properties import *

from kivy.uix.accordion import Accordion 
from kivy.uix.accordion import AccordionItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

import logging

logger = logging.getLogger("purikura.kiosk")

# default place for config files
config.load('/home/mjolnir/git/PURIKURA/config/')

# load our templates
module = os.path.dirname(os.path.abspath(__file__))
Builder.load_file(os.path.join(module, 'kiosk-common.kv'))
Builder.load_file(os.path.join(module, 'kiosk-composite.kv'))
Builder.load_file(os.path.join(module, 'kiosk-single.kv'))
del module

MAXIMUM_PRINTS = config.kiosk.getint('kiosk', 'max-prints')
dbus_name = config.service.get('camera', 'dbus-name')
dbus_path = config.service.get('camera', 'dbus-path')

# dbus  :D
#DBusGMainLoop(set_as_default=True)
#bus = dbus.SessionBus()
#pb_obj = bus.get_object(dbus_name, dbus_path)
#pb_iface = dbus.Interface(pb_obj, dbus_interface=dbus_name)


def handle_print_number_error(value):
    if value < 1:
        return 1
    elif value > MAXIMUM_PRINTS:
        return MAXIMUM_PRINTS


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


class IconAccordionItem(AccordionItem):
    icon_source = StringProperty()
    icon_size = ListProperty()


OFFSET = 172


jpath = os.path.join
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

        # defaults to the hidden state
        self.focus_widget = Image(source=image_path('images/loading.gif'))
        self.focus_widget.allow_stretch = True
        self.focus_widget.x = center_x - OFFSET
        self.focus_widget.y = -1000
        self.focus_widget.size_hint = None, None
        self.focus_widget.size = self.small_preview_size
        self.focus_widget.bind(on_touch_down=self.on_image_touch)
        self.layout.add_widget(self.focus_widget)

        self.preview_widget = Image(source='capture.jpg', nocache=False)
        self.preview_widget.allow_stretch = True
        self.preview_widget.x = center_x - OFFSET
        self.preview_widget.y = 0
        self.preview_widget.size_hint = None, None
        self.preview_widget.size = (100, 100)
        self.preview_widget.bind(on_touch_down=self.on_image_touch)
        self.layout.add_widget(self.preview_widget)

        def update_preview(widget, mouse_point):
            if widget.collide_point(mouse_point.x, mouse_point.y):
                #pb_iface.capture_preview()
                if os.path.exists('preview.jpg'):
                    widget.source = 'preview.jpg'
                    widget.reload()

        self.preview_widget.bind(on_touch_down=update_preview)

        #pb_iface.connect_to_signal('preview_updated', update_preview)

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


import smtplib
import threading
import pickle

sender = config.kiosk.get('email', 'sender')
subject = config.kiosk.get('email', 'subject')
auth_file = '/home/mjolnir/git/PURIKURA/secrets'


class SenderThread(threading.Thread):
    def __init__(self, address, filename):
        threading.Thread.__init__(self)
        self.address = address
        self.filename = filename

    def run(self):
        import email

        msg = email.MIMEMultipart.MIMEMultipart('mixed')
        msg['subject'] = subject
        msg['from'] = sender
        msg['to'] = self.address

        body = email.mime.Text.MIMEText('Here\'s your photo!\n\nThank you!\n\n')
        msg.attach(body)

        file_msg = email.mime.base.MIMEBase('image', 'jpeg')
        file_msg.set_payload(open(self.filename).read())
        email.encoders.encode_base64(file_msg)
        file_msg.add_header(
            'Content-Disposition',
            'attachment;filname=photo.jpg')
        msg.attach(file_msg)

        with open(auth_file) as fh:
            auth = pickle.load(fh)
            auth = auth['smtp']

        with open('email.log', 'a') as fh:
            fh.write('{}\t{}\n'.format(self.address, self.filename))

        smtpout = smtplib.SMTP(auth['host'])
        smtpout.login(auth['username'], auth['password'])

        auth = None

        smtpout.sendmail(sender, [self.address], msg.as_string())
        smtpout.quit()


class SharingControls(FloatLayout):
    prints = BoundedNumericProperty(1, min=1, max=MAXIMUM_PRINTS,
                                    errorhandler=handle_print_number_error)

    email_addressee = StringProperty('')
    twitter_acct = StringProperty('@kilbuckcreekphoto')
    filename = StringProperty()

    def disable(self):
        def derp(*arg):
            return False

        for widget in self.children:
            widget.on_touch_down = derp
            widget.on_touch_up = derp
            widget.on_touch_motion = derp

    def do_print(self, popup, widget):
        popup.dismiss()

        for i in range(self.prints):
            filename = '/home/mjolnir/smb-printsrv/temp-preint-{}.png'.format(i)
            shutil.copyfile(self.filename, filename)

        layout = BoxLayout(orientation='vertical')
        label = Label(
            text='Your prints will be ready soon!',
            font_size=30)
        button = Button(
            text='Awesome!',
            font_size=30,
            background_color=(0, 1, 0, 1))
        layout.add_widget(label)
        layout.add_widget(button)

        popup = Popup(
            title='Just thought you should know...',
            content=layout,
            size_hint=(.5, .5))

        button.bind(on_release=popup.dismiss)

        popup.open()


    def do_email(self, popup, address, filename, widget):
        thread = SenderThread(address, filename)
        thread.daemon = True
        thread.start()
        popup.dismiss()

        layout = BoxLayout(orientation='vertical')
        label = Label(
            text='Just sent this image to:\n\n{}'.format(address),
            font_size=30)
        button = Button(
            text='Awesome!',
            font_size=30,
            background_color=(0, 1, 0, 1))
        layout.add_widget(label)
        layout.add_widget(button)

        popup = Popup(
            title='Just thought you should know...',
            content=layout,
            size_hint=(.5, .5))

        button.bind(on_release=popup.dismiss)

        from kivy.core.window import Window

        Window.release_all_keyboards()

        self.reset_email_textinput()

        popup.open()


    def confirm_print(self):
        layout0 = BoxLayout(orientation='vertical')
        layout1 = BoxLayout(orientation='horizontal')
        label = Label(
            text='You want to print {} copies?'.format(self.prints),
            font_size=30)
        button0 = Button(
            text='Just do it!',
            font_size=30,
            background_color=(0, 1, 0, 1))
        button1 = Button(
            text='No',
            font_size=30,
            background_color=(1, 0, 0, 1))
        layout1.add_widget(button1)
        layout1.add_widget(button0)
        layout0.add_widget(label)
        layout0.add_widget(layout1)

        popup = Popup(
            title='Are you sure?',
            content=layout0,
            size_hint=(.5, .5),
            auto_dismiss=False)

        button0.bind(on_release=partial(
            self.do_print, popup))

        button1.bind(on_release=popup.dismiss)

        popup.open()


    def confirm_address(self):
        if not self.email_addressee:
            layout = BoxLayout(orientation='vertical')
            label = Label(
                text='Please enter an email address',
                font_size=30)
            button = Button(
                text='ok!',
                font_size=30,
                background_color=(0, 1, 0, 1))
            layout.add_widget(label)
            layout.add_widget(button)

            popup = Popup(
                title='Oops!',
                content=layout,
                size_hint=(.5, .5))

            button.bind(on_release=popup.dismiss)

        else:
            layout0 = BoxLayout(orientation='vertical')
            layout1 = BoxLayout(orientation='horizontal')
            label = Label(
                text='Is this email address correct?\n\n{}'.format(
                    self.email_addressee),
                font_size=30)
            button0 = Button(
                text='Yes',
                font_size=30,
                background_color=(0, 1, 0, 1))
            button1 = Button(
                text='No',
                font_size=30,
                background_color=(1, 0, 0, 1))
            layout1.add_widget(button1)
            layout1.add_widget(button0)
            layout0.add_widget(label)
            layout0.add_widget(layout1)

            popup = Popup(
                title='Question',
                content=layout0,
                size_hint=(.5, .5),
                auto_dismiss=False)

            button0.bind(on_release=partial(
                self.do_email, popup, str(self.email_addressee),
                str(self.filename)))

            button1.bind(on_release=popup.dismiss)

        popup.open()

    def check_email_text(self, widget):
        self.email_addressee = widget.text

    def add_print(self):
        self.prints += 1

    def remove_print(self):
        self.prints -= 1

    def change_vkeyboard_email(self):
        Config.set('kivy', 'keyboard_mode', 'dock')
        Config.set('kivy', 'keyboard_layout', 'email')

    def reset_email_textinput(self):
        self.email_textinput = ''

    def change_vkeyboard_normal(self):
        Config.set('kivy', 'keyboard_layout', DEFAULT_VKEYBOARD_LAYOUT)


