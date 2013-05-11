import threading



class Broker(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(Broker, self).__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def run(self):
        while self.running:
            task = self.queue.get()
            self.process(task)
            self.queue.task_done()

    def process(self, task):
        pass

