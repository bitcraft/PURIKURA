import shutil
from functools import partial

from kivy.uix.accordion import Accordion
from kivy.uix.accordion import AccordionItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.properties import *

from ..smtp import SenderThread
from ..config import Config as pkConfig

MAXIMUM_PRINTS = pkConfig.getint('kiosk', 'max-prints')


def handle_print_number_error(value):
    if value < 1:
        return 1
    elif value > MAXIMUM_PRINTS:
        return MAXIMUM_PRINTS


class IconAccordionItem(AccordionItem):
    icon_source = StringProperty()
    icon_size = ListProperty()


class SharingControls(FloatLayout):
    prints = BoundedNumericProperty(1, min=1, max=MAXIMUM_PRINTS,
                                    errorhandler=handle_print_number_error)

    email_addressee = StringProperty('')
    twitter_acct = StringProperty(
        pkConfig.get('twitter', 'account')
    )
    filename = StringProperty()

    def __init__(self, *args, **kwargs):
        super(SharingControls, self).__init__(*args, **kwargs)

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

