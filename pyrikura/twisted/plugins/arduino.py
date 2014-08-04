from zope.interface import implements
from twisted.plugin import IPlugin
from pyrikura import ipyrikura


class Arduino(object):
    implements(IPlugin, ipyrikura.IFileOp)