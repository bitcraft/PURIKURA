import os

from pyrikura.plugin import Plugin


class Deleter(Plugin):
    def process(self, msg, sender):
        os.unlink(msg)
        self.publish([msg])
