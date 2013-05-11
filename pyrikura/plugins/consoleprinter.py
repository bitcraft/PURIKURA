from pyrikura.plugin import Plugin
import sys



class ConsolePrinter(Plugin):
    def process(self, msg, sender):
        sys.stdout.write(msg + '\n')
        sys.stdout.flush()
