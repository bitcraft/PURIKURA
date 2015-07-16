from twisted.plugin import IPlugin

from zope.interface import implements
from pyrikura import ipyrikura


class Arduino(object):
    implements(IPlugin, ipyrikura.IFileOp)
