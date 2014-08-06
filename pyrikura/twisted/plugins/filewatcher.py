from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from pyrikura import ipyrikura

import os


class FileWatcherFactory(object):
    implements(IPlugin)

    def new(self, *args, **kwargs):
        return FileWatcher(*args, **kwargs)


class FileWatcher(object):
    """
    Simple watcher that uses a glob to track new files
    This class will publish paths to new images
    """
    implements(ipyrikura.IFileOp)

    def __init__(self, path, regex=None):
        self._path = path
        self._regex = regex
        self._queue = defer.DeferredQueue()
        self._seen = set()

    def reset(self):
        self._seen = set()

    def tick(self, td=0.0):
        if self._regex is None:
            files = set(os.listdir(self._path))
        else:
            files = set()
            for fn in os.listdir(self._path):
                match = self._regex.match(fn)
                if match:
                    files.add(fn)

        # get files that have not been seen before and publish them
        pub = [os.path.join(self._path, i) for i in files - self._seen]

        # add the new items to the seen set
        self._seen.update(files)

        return self._queue


factory = FileWatcherFactory()
