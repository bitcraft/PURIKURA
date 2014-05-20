import re
import subprocess

from pyrikura.plugin import Plugin


class Scripter(Plugin):
    """
    given a list of strings, process them in order with the supplied argument

    {msg} becomes the content of the message
    """
    msg_re = re.compile('{msg}', re.I)


    def __init__(self, program):
        self._program = program

    def process(self, msg, sender):
        for line in self._program:
            line = self.msg_re.sub(line, msg)
            subprocess.call(line.split())
