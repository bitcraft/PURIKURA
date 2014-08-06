from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from pyrikura import ipyrikura

import pickle
import twython


class ImageTweetFactory(object):
    implements(IPlugin)

    def new(self, *args, **kwargs):
        return ImageTweet(*args, **kwargs)


class ImageTweet(object):
    implements(ipyrikura.IFileOp)

    def __init__(self):
        self._auth = None
        self._conn = None

    def auth(self, auth_file, *arg, **kwarg):
        with open(auth_file) as fh:
            self._auth = pickle.load(fh)['twitter']
        self.connect()

    def process(self, msg, sender=None):
        def send():
            self._conn.update_status_with_media(msg, status='Test!')

        d = defer.Deferred()
        d.addCallback(send)
        return d

    def connect(self):
        self._conn = twython.Twython(**self._auth)


factory = ImageTweetFactory
