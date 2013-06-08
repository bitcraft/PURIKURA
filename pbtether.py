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

from pyrikura.workflow import Node
import logging
import argparse
import os
import itertools
import re
import pickle
import time


event = 'test'

settings = {}
settings['shutter_sound'] = os.path.join('sounds', 'bell.wav')
settings['reprint_sound'] = os.path.join('sounds', 'long_bell.wav')
settings['printsrv']   = '/home/mjolnir/smb-printsrv'
settings['template']   = 'templates/2x6vintage.template'
settings['thumbnails'] = '/home/mjolnir/events/{}/small'.format(event)
settings['detail']     = '/home/mjolnir/events/{}/medium'.format(event)
settings['originals']  = '/home/mjolnir/events/{}/originals'.format(event)
settings['composites'] = '/home/mjolnir/events/{}/composites/'.format(event)
settings['temp_image'] = 'capture.jpg'


paths = ('thumbnails', 'detail', 'originals', 'composites')


for path in [ settings[i] for i in paths ]:
    if not os.path.exists(path):
        os.makedirs(path)

def build():
    arduino = Node('Arduino', '/dev/ttyACM0', 9600)

    beacon1 = Node('Repeater', 1000, 60)
    beacon2 = Node('Repeater', 4, delay=10)

    ringer = Node('Repeater', 4, delay=3)
    shutter = Node('Repeater', 1, interval=4)

    tether = Node('Tether')
    composer = Node('Composer', template=settings['template'])
    stdout = Node('ConsolePrinter')
    archiver1 = Node('FileCopy', dest=settings['originals'])
    archiver2 = Node('FileCopy', dest=settings['composites'])
    thumbnailer1 = Node('Thumbnailer', size='300x300', dest=settings['thumbnails'])
    thumbnailer2 = Node('Thumbnailer', size='768x768', dest=settings['detail'])
    spooler = Node('FileCopy', dest=settings['printsrv'])
    twitter = Node('Twitter', 'secrets')
    sound1 = Node('Sound', settings['shutter_sound'], 2)
    sound2 = Node('Sound', settings['reprint_sound'], 3)

    beacon2.subscribe(arduino)
    sound2.subscribe(arduino)

    ringer.subscribe(beacon2)

    sound1.subscribe(ringer)
    shutter.subscribe(ringer)
   
    tether.subscribe(shutter)

    #repeater.subscribe(arduino)

    composer.subscribe(tether)
    archiver1.subscribe(tether)

    thumbnailer1.subscribe(archiver1)
    thumbnailer2.subscribe(archiver1)

    archiver2.subscribe(composer)
    #spooler.subscribe(composer)
    #twitter.subscribe(composer)

    # the order of this list determines priority of updates
    return [ beacon1, beacon2, ringer, sound1, sound2, arduino,
             stdout, composer, spooler, archiver1, archiver2,
             tether, shutter, twitter, thumbnailer1, thumbnailer2 ]


def run():
    logging.basicConfig(level=logging.INFO)

    os.chdir('/home/mjolnir/git/PURIKURA')

    # H A N D L E  P L U G I N S
    pm = PluginManager()
    pm.setPluginPlaces(['./pyrikura/plugins'])
    pm.collectPlugins()

    for pi in pm.getAllPlugins():
        logging.info('loading plugin %s', pi.name)
        pm.activatePluginByName(pi.name)

    brokers = {}
    nodes = build()
    head = nodes[0]

    for node in nodes:
        brokers[node] = node.load(pm)

    for node, broker in brokers.items():
        for other in node._listening:
            broker.subscribe(brokers[other])

    # testing!
    #brokers[nodes[0]].process(['hello!'])

    for broker in itertools.cycle(brokers.values()):
        broker.update()
        time.sleep(.05)


profile = False
if __name__ == '__main__':
    if profile:
        import cProfile
        import pstats

        try:
            cProfile.run('run()', 'results.prof')
        except KeyboardInterrupt:
            pass

        p = pstats.Stats("results.prof")
        p.strip_dirs()
        p.sort_stats('time').print_stats(20)
        
    else:
        run()
