from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from twisted.internet import threads
from pyrikura import ipyrikura

import os


class FileDeleteFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)

    def new(self, *args, **kwargs):
        return FileDelete(*args, **kwargs)


class FileDelete(object):
    implements(ipyrikura.IFileOp)

    def process(self, msg, sender=None):
        return threads.deferToThread(os.unlink, msg)


factory = FileDeleteFactory()
