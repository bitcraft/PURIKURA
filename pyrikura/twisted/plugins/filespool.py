from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from pyrikura import ipyrikura

import subprocess32


class FileSpool(object):
    implements(ipyrikura.IFileOp)

    def __init__(self):
        self.print_command = 'lpr'

    def process(self, msg, sender=None):
        cmd = [self.print_command, msg]
        return threads.deferToThread(subprocess.call, cmd)


class FileSpoolFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)
    __plugin__ = FileSpool

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)


factory = FileSpoolFactory()
