import subprocess

from pyrikura.plugin import Plugin


class FileSpool(Plugin):
    def process(self, msg, sender):
        cmd = ['lpr', msg]
        subprocess.call(cmd)
        self.publish([msg])
