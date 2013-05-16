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



event_name = 'test'

settings = {}
settings['shutter_sound'] = os.path.join('sounds', 'bell.wav')
settings['printsrv'] = os.path.join('/', 'home', 'mjolnir', 'smb-printsrv')
#settings['template'] = os.path.join('templates', 'polaroid0.template')
settings['template'] = os.path.join('templates', '2x6vintage.template')
settings['originals'] = os.path.join('/', 'home', 'mjolnir', 'events', event_name, 'originals')
settings['temp_image'] = 'capture.jpg'


def build():
    arduino = Node('Arduino', '/dev/ttyACM0', 9600)
    repeater = Node('Repeater', 4, 2)
    tether = Node('Tether')
    composer = Node('Composer', template=settings['template'])
    stdout = Node('ConsolePrinter')
    archiver = Node('FileCopy', dest=settings['originals'])
    spooler = Node('FileCopy', dest=settings['printsrv'])
    twitter = Node('Twitter', 'twitter.secrets')

    repeater.subscribe(arduino)
    tether.subscribe(repeater)
    composer.subscribe(tether)
    archiver.subscribe(tether)
    spooler.subscribe(composer)
    #twitter.subscribe(composer)

    return [arduino, stdout, composer, spooler, archiver, tether, twitter,
            repeater]


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

    start = time.time()
    last_time = 0
    shots = 0
    last_trigger = 0
    for broker in itertools.cycle(brokers.values()):
        now = time.time()
        if now - last_trigger >= 10:
            last_trigger = now
            brokers[head].publish(['capture'])
            print "TRIGGER"

        if last_time != int(now-start):
            last_time = int(now - start)
            print last_time

        broker.update()

    #eyefi = Watcher(eyefi_incoming, re.compile('.*\.jpg$', re.I))
    #arduino = Arduino('/dev/ttyACM0', 9600)


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
