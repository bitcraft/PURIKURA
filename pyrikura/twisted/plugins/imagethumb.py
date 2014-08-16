from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from twisted.internet import threads
from pyrikura import ipyrikura
from PIL import Image

import os


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

    def thumbnail(self, filename):
        image = Image.open(filename)
        image.thumbnail(self.size)
        image.save(self.destination)
        return filename, self.destination

    def process(self, filename):
        if filename is None:
            raise ValueError
        return threads.deferToThread(self.thumbnail, filename)


class ImageThumbFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)
    __plugin__ = ImageThumb

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)

factory = ImageThumbFactory()
