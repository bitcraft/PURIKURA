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
            shlex.split(
                thumbnail_cmd.format(hint, original, size, size, new_path)))


class ThumbnailerBroker(Broker):
    def process(self, msg, sender=None):
        thread = ExecutionThread(msg, self.dest, self.size)
        thread.daemon = True
        thread.start()


class Thumbnailer(pl):
    _decendant = ThumbnailerBroker

