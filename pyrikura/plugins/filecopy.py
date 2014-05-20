import os
import shutil

from pyrikura.broker import Broker
from pyrikura.plugin import Plugin


class FileCopyBroker(Broker):
    def _do_copy(self, path, dest):
        shutil.copyfile(path, dest)

    def process(self, msg, sender=None):
        try:
            overwrite = self.overwrite
        except AttributeError:
            overwrite = False

        new_path = os.path.join(self.dest, os.path.basename(msg))

        if not overwrite and os.path.exists(new_path):
            i = 1
            root, ext = os.path.splitext(new_path)
            new_path = "{0}-{1:04d}{2}".format(root, i, ext)
            while os.path.exists(new_path):
                i += 1
                new_path = "{0}-{1:04d}{2}".format(root, i, ext)

        self._do_copy(msg, new_path)
        self.publish([new_path])


class FileCopy(Plugin):
    _decendant = FileCopyBroker
