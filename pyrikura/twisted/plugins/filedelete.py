from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from twisted.internet import threads
from pyrikura import ipyrikura

import os


class FileDelete(object):
    implements(ipyrikura.IFileOp)

    def process(self, msg, sender=None):
        return threads.deferToThread(os.unlink, msg)


class FileDeleteFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)
    __plugin__ = FileDelete

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)

factory = FileDeleteFactory()
