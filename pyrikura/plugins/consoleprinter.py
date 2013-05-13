from pyrikura.plugin import Plugin
from pyrikura.broker import Broker
import sys



class ConsolePrinterBroker(Broker):
    def process(self, msg, sender):
        sys.stdout.write(msg + '\n')
        sys.stdout.flush()


class ConsolePrinter(Plugin):
    _decendant = ConsolePrinterBroker
