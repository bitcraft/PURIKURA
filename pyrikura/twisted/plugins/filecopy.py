from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer, threads
from pyrikura import ipyrikura

import os
import shutil


class FileCopy(object):
    implements(ipyrikura.IFileOp)

    def __init__(self, dest, **kwargs):
        self.dest = dest
        self.overwrite = kwargs.get('overwrite', False)
        self.delete = kwargs.get('delete', False)

    def process(self, filename):
        def func():
            path = os.path.join(self.dest, os.path.basename(filename))
            if not self.overwrite and os.path.exists(path):
                i = 1
                root, ext = os.path.splitext(path)
                path = "{0}-{1:04d}{2}".format(root, i, ext)
                while os.path.exists(path):
                    i += 1
                    path = "{0}-{1:04d}{2}".format(root, i, ext)
            
            if self.delete:
                shutil.move(filename, path)
            else:
                shutil.copyfile(filename, path)
            return path

        return threads.deferToThread(func)


class FileCopyFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)
    __plugin__ = FileCopy

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)

factory = FileCopyFactory()


