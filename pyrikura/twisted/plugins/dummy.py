from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from pyrikura import ipyrikura

import os


class PassThrough(object):
    implements(ipyrikura.IFileOp)

    def process(self, filename):
        return defer.succeed(filename)


class AddString(object):
    implements(ipyrikura.IFileOp)

    def __init__(self, string):
        self._string = string

    def process(self, filename):
        root, ext = os.path.splitext(filename)
        return defer.succeed(root + self._string + ext)


class DummyFactory(object):
    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)


class PassThroughFactory(DummyFactory):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)
    __plugin__ = PassThrough


class AddStringFactory(DummyFactory):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)
    __plugin__ = AddString


factory0 = PassThroughFactory()
factory1 = AddStringFactory()

