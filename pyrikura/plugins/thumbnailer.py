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

'''
simple thumbnailer.

spawns a thread that launches a childprocess that resizes the image.
creates a square crop to the size passed
'''


from pyrikura.broker import Broker
from pyrikura.plugin import Plugin as pl
import subprocess, os, threading, shlex


thumbnail_cmd = 'convert -define jpeg:size={} {} -thumbnail {}^ -gravity center -extent {} {}'


class ExecutionThread(threading.Thread):
    def __init__(self, *args):
        super(ExecutionThread, self).__init__()
        self.args = args

    def run(self):
        original, dest, size = self.args
        new_path = os.path.join(dest, os.path.basename(original))

        hint = '600x600'

        subprocess.call(
            shlex.split(thumbnail_cmd.format(hint, original, size, size, new_path)))

class ThumbnailerBroker(Broker):

    def process(self, msg, sender=None):
        thread = ExecutionThread(msg, self.dest, self.size)
        thread.daemon = True
        thread.start()

class Thumbnailer(pl):
    _decendant = ThumbnailerBroker

