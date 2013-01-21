from pubsub import pubsub


class ConsolePrinter(pubsub):
    def process(self, msg, sender):
        print msg
