from pyrikura.plugin import Plugin
import os



class Deleter(Plugin):
    def process(self, msg, sender):
        os.unlink(msg)
        self.publish([msg])
