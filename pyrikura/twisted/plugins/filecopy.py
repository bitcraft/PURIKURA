from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer, threads
from pyrikura import ipyrikura

import os
import shutil


class FileCopyFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)

    def new(self, *args, **kwargs):
        return FileCopy(*args, **kwargs)


class FileCopy(object):
    implements(ipyrikura.IFileOp)

    def __init__(self, dest, **kwargs):
        self.dest = dest
        self.overwrite = kwargs.get('overwrite', False)

    def process(self, msg, sender=None):
        new_path = os.path.join(self.dest, os.path.basename(msg))

        if not self.overwrite and os.path.exists(new_path):
            i = 1
            root, ext = os.path.splitext(new_path)
            new_path = "{0}-{1:04d}{2}".format(root, i, ext)
            while os.path.exists(new_path):
                i += 1
                new_path = "{0}-{1:04d}{2}".format(root, i, ext)

        return threads.deferToThread(shutil.copyfile, msg, new_path)


factory = FileCopyFactory()
