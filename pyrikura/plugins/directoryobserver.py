from pyrikura.plugin import Plugin
import os



class Watcher(Plugin):
    """
    Simple watcher that uses a glob to track new files
    This class will publish paths to new images
    """

    def __init__(self, path, regex=None):
        super(Watcher, self).__init__()
        self._path = path
        self._regex = regex

    def OnActivate(self):
        self.reset()

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
        pub = [ os.path.join(self._path, i) for i in files - self._seen ]
        self.publish(pub)

        # add the new items to the seen set
        self._seen.update(files)
