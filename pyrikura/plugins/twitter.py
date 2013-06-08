from pyrikura.broker import Broker
from pyrikura.plugin import Plugin
import twython
import pickle



class PBTwitterBroker(Broker):
    def __init__(self, auth_file, *arg, **kwarg):
        super(PBTwitterBroker, self).__init__(*arg, **kwarg)
        with open(auth_file) as fh:
            self._auth = pickle.load(fh)['twitter']
        self.connect()

    def process(self, msg, sender=None):
        self.twitter.update_status_with_media(msg, status='Test!')

    def connect(self):
        self.twitter = twython.Twython(**self._auth)


class PBTwitter(Plugin):
    _decendant = PBTwitterBroker
