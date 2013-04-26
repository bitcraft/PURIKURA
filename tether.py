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


settings = {}
settings['shutter_sound'] = os.path.join('sounds', 'beep.wav')
settings['printsrv'] = os.path.join('/', 'home', 'mjolnir', 'smb-printsrv')
settings['template'] = os.path.join('templates', 'polaroid0.template')


# protocol
trigger_command = 1         # when button is pressed to start picture seq.
shutter_command = 2         # command to cause camera shutter
reset_command = 6           # when photos are out of sequence
set_busy = 7                # when camera is actively taking photos
set_not_busy = 8            # when camera is no longer taking pictures

# arduino control
arduinoPortNumber = 6

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


class Tether(pubsub):
    """
    waits for a message and publishes captured jpg images
    """

    def __init__(self, camera):
        super(Tether, self).__init__()
        self.camera = camera

    def process(self, msg, sender):
        camera.capture(msg)
        self.publish([msg])


if __name__ == '__main__':
    pygame.init()
    pygame.mixer.init()

    camera = PBCamera()

    # setup our processing workflow
    tether = Tether(camera)
    beeper = Beeper(settings['shutter_sound'])
    template = Template(settings['template'])
    print_copier = Copier(output=settings['printsrv'], overwrite=True)

    # connect the dots
    beeper.subscribe(tether)
    template.subscribe(tether)
    print_copier.subscribe(template)

    while(1):
        tether.process('capture.jpg', None)
        time.sleep(3)

