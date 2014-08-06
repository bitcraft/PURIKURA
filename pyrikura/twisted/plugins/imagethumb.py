from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from pyrikura import ipyrikura

import subprocess
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

    def process(self, msg, sender=None):
        def thumbnail():
            hint = '600x600'
            new_path = os.path.join(destination, os.path.basename(filename))
            thumbnail_cmd.format(hint, filename, size, size, new_path)
            subprocess.call(shlex.split(thumbnail_cmd))

        d = defer.Deferred()
        d.addCallback(thumbnail)
        return d

factory = ImageThumbFactory()
