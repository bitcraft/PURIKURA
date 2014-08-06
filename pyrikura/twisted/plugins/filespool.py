from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from pyrikura import ipyrikura

import subprocess


class FileSpoolFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)

    def new(self, *args, **kwargs):
        return FileSpool(*args, **kwargs)


class FileSpool(object):
    implements(ipyrikura.IFileOp)

    def __init__(self):
        self.print_command = 'lpr'

    def process(self, msg, sender=None):
        cmd = [self.print_command, msg]
        d = defer.Deferred
        d.addCallback(subprocess.call, cmd)
        return d


factory = FileSpoolFactory()