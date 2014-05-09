from pyrikura.plugin import Plugin
import subprocess


class FileSpool(Plugin):
    def process(self, msg, sender):
        cmd = ['lpr', msg]
        subprocess.call(cmd)
        print
        'printing {0}'.format(msg)
        self.publish([msg])
