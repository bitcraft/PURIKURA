from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from twisted.internet import threads
from pyrikura import ipyrikura

import subprocess32
import threading
import shlex
import os

thumbnail_cmd = 'convert -define jpeg:size={} {} -thumbnail {}^ -gravity center -extent {} {}'


class ImageThumbFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)

    def new(self, *args, **kwargs):
        return ImageThumb(*args, **kwargs)


class ImageThumb(object):
    """
    simple thumbnailer.

    spawns a thread that launches a childprocess that resizes the image.
    creates a square crop to the size passed
    """
    implements(ipyrikura.IFileOp)

    def __init__(self, size):
        self.size = size

    def process(self, msg, sender=None):
        def thumbnail():
            hint = '600x600'
            size = self.self
            new_path = os.path.join(destination, os.path.basename(filename))
            cmd = thumbnail_cmd.format(hint, filename, size, size, new_path)
            subprocess.call(shlex.split(cmd))
        return threads.deferToThread(thumbnail)

factory = ImageThumbFactory()
