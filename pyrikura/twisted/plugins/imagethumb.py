from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from twisted.internet import threads
from pyrikura import ipyrikura

import subprocess32 as subprocess
import threading
import shlex
import os

thumbnail_cmd = 'convert -define jpeg:size={} {} -thumbnail {}^ -gravity center -extent {} {}'


class ImageThumb(object):
    """
    simple thumbnailer.

    spawns a thread that launches a childprocess that resizes the image.
    creates a square crop to the size passed
    """
    implements(ipyrikura.IFileOp)

    def __init__(self, size, destination):
        self.size = size
        self.destination = destination

    def process(self, filename):
        def thumbnail():
            hint = '600x600'
            path = self.destination
            cmd = thumbnail_cmd.format(hint, filename, self.size, self.size, path)
            subprocess.call(shlex.split(cmd))
            return path
        return threads.deferToThread(thumbnail)


class ImageThumbFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)
    __plugin__ = ImageThumb

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)

factory = ImageThumbFactory()
