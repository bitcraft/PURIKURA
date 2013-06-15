import threading
import itertools
import Queue



class Broker(object):
    def __init__(self, *arg, **kwarg):
        self.queue = Queue.Queue()
        self._subscribers = []
        self._error_subscribers = []
        for key, value in kwarg.items():
            setattr(self, key, value)

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def process(self, msg, sender=None):
        pass

    def subscribe(self, other):
        other._subscribers.append(self)

    def subscribe_error(self, other):
        other._error_subscribers.append(self)

    def error(self):
        for i in iterable:
            for other in self._error_subscribers:
                other.process(i, self)

    def publish(self, iterable):
        for i in iterable:
            for other in self._subscribers:
                other.process(i, self)

    def update(self, delta=0):
        pass


class ThreadedBroker(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(Broker, self).__init__()
        self.queue = Queue.Queue()
        self._listening = []
        self._running = False
        for key, value in kwargs.items():
            setattr(self, key, value)

    def publish(self, iterable):
        [ self.queue.put(i) for i in iterable ]

    def subscribe(self, other):
        self._listening.append(other)

    def run(self):
        self._running = True
        for broker in itertools.cycle(self._listening):
            if self._running == False:
                break

            if broker:
                task = broker.queue.get()
                self.process(task)
                broker.queue.task_done()

    def process(self, task):
        pass

