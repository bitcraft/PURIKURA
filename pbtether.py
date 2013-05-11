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

Very basic script that triggers a sequence of images on a tethered camera
and saves the output as jpeg images.

This script is intended to be used in conjunction with other software that
collectively creates a seemless photo booth experience.
"""

from yapsy.PluginManager import PluginManager

import logging
import argparse
import os



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
servo_command = 3
servo_response = 4
reset_command = 6           # when photos are out of sequence


def build():
    import pickle

    arduino = Node('Arduino')
    tether = Node('Tether')
    composer = Node('Composer')

    composer.subscribe(tether)
    spooler.subscribe(composer)

    return pickle.dump(arduino)


if __name__ == '__main__':
    import re

    logging.basicConfig(level=logging.INFO)

    os.chdir('/home/mjolnir/git/PURIKURA')

    # H A N D L E  P L U G I N S
    pm = PluginManager()
    pm.setPluginPlaces(['./pyrikura/plugins'])
    pm.collectPlugins()

    for pi in pm.getAllPlugins():
        logging.info('loading plugin %s', pi.name)
        pm.activatePluginByName(pi.name)

    arduino = pm.getPluginByName('Arduino').plugin_object.new()
    #tether0 = pm.getPluginByName('tether').new()
    #spooler = pm.getPluginByName('spooler').new()
    #composer = pm.getPluginByName('composer').new(settings['template'])

    #eyefi = Watcher(eyefi_incoming, re.compile('.*\.jpg$', re.I))
    #arduino = Arduino('/dev/ttyACM0', 9600)
