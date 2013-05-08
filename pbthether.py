#!/usr/bin/env python
"""
*
*   copyright: 2012 Leif Theden <leif.theden@gmail.com>
*   license: GPL-3
*
*   This file is part of pyrikura/purikura.
*
*   pyrikura is free software: you can redistribute it and/or modify
*   it under the terms of the GNU General Public License as published by
*   the Free Software Foundation, either version 3 of the License, or
*   (at your option) any later version.
*
*   pyrikura is distributed in the hope that it will be useful,
*   but WITHOUT ANY WARRANTY; without even the implied warranty of
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*   GNU General Public License for more details.
*
*   You should have received a copy of the GNU General Public License
*   along with pyrikura.  If not, see <http://www.gnu.org/licenses/>.
*
"""

"""
Tethered Camera Controller for Photo Booth

Very basic script that triggers a sequence of images on a tethered SDL camera
and saves the output as jpeg images.

This script is intended to be used in conjunction with other software that
collectively create a seemless photo booth experience.
"""

from pyrikura import *
import piggyphoto
import argparse
import subprocess
import os
import pygame
import time
import serial


os.chdir('/home/mjolnir/git/PURIKURA')

event_name = 'test'


settings = {}
settings['shutter_sound'] = os.path.join('sounds', 'bell.wav')
settings['printsrv'] = os.path.join('/', 'home', 'mjolnir', 'smb-printsrv')
settings['template'] = os.path.join('templates', 'polaroid0.template')
settings['originals'] = os.path.join('/', 'home', 'mjolnir', 'events', \
                        event_name, 'originals')

settings['temp_image'] = 'capture.jpg'


# protocol
trigger_command = 1         # when button is pressed to start picture seq.
shutter_command = 2         # command to cause camera shutter
reset_command = 6           # when photos are out of sequence
set_busy = 7                # when camera is actively taking photos
set_not_busy = 8            # when camera is no longer taking pictures

# photo taking preferences
total_pictures = 4
shutter_delay = 5000    # delay between photos
trigger_delay = 3000    # delay before 1st photo after trigger

# misc.
current_picture = 9999  # don't change this


class PBCamera(object):
    def __init__(self):
        self.init_camera()
        
    def capture(self, filename=None):
        self.camera.capture_image(filename)

    def init_camera(self):
        c = piggyphoto.camera()
        c.leave_locked()
        self.camera = c


class Beeper(pubsub):
    def __init__(self, filename):
        super(Beeper, self).__init__()
        self.sound = pygame.mixer.Sound(filename)
        
    def process(self, msg, sender):
        self.sound.play()


class Arduino(pubsub):
    def __init__(self, *arg):
        super(Arduino, self).__init__()
        self.serial = serial.Serial(*arg, timeout=0)
        time.sleep(2)
        self.clear()

    def clear(self):
        # clear any buffered data
        while self.serial.read():
            pass

    def tick(self):
        byte = self.serial.read(1)
        self.publish([byte])


class Translate(pubsub):
    def process(self, msg, sender):
        if msg == chr(1): self.publish([settings['temp_image']])


class Tether(pubsub):
    """
    waits for a message and publishes captured jpg images
    """

    def __init__(self, camera, arduino):
        super(Tether, self).__init__()
        self.arduino = arduino
        self.camera = camera
        self.sound = pygame.mixer.Sound(settings['shutter_sound'])

    def process(self, msg, sender):
        self.sound.play()
        time.sleep(2)
        self.sound.play()
        time.sleep(2)
        self.sound.play()
        time.sleep(2)
        self.sound.play()
        camera.capture(msg)
        self.publish([msg])
        self.arduino.clear()


if __name__ == '__main__':
    import re

    pygame.init()
    pygame.mixer.init()

    camera = PBCamera()
    debug = ConsolePrinter()
    eyefi_incoming = '/home/iiid/incoming/0018562a8795'


    # setup our processing workflow
    eyefi = Watcher(eyefi_incoming, re.compile('.*\.jpg$', re.I))
    translate = Translate()
    arduino = Arduino('/dev/ttyACM0', 9600)
    tether = Tether(camera, arduino)
    beeper = Beeper(settings['shutter_sound'])
    template0 = Template(settings['template'], filename='composite0.png')
    template1 = Template(settings['template'], filename='composite1.png')
    print_copier = Copier(output=settings['printsrv'], overwrite=True)
    original_copier = Copier(output=settings['originals'])

    # connect the dots
    translate.subscribe(arduino)
    tether.subscribe(translate)
    template0.subscribe(tether)
    #template1.subscribe(eyefi)
    original_copier.subscribe(tether)
    #original_copier.subscribe(eyefi)
    print_copier.subscribe(template0)
    #print_copier.subscribe(template1)

    while(1):
        arduino.tick()
        #eyefi.tick()
