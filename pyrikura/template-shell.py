from pubsub import pubsub
import sys, subprocess, ConfigParser

convert = '/usr/bin/convert'


def resize(image, (x, y)):
    """
    resize an image using a process (imagemagick)
    """
    fn = 'resized.miff'
    cmd = '{0} -scale {1}x{2} {3}'.format(convert, x, y, fn)
    subprocess.call(cmd.split())
    return fn


class Scripter(pubsub):
    """
    uses templates and images to create print layouts
    """

    def __init__(self, template):
        self._config = ConfigParser.ConfigParser()
        self._config.read(template)

    def process(self, msg, sender):
        """
        the message can be a sequence or dictionary:
        
        sequence:
            each image will be added to template in sorted order by heading

        dictionary:
            each image will be added to template according to name

        """
        if isinstance(msg, list):
            images = msg[:]
            for section in self._config.sections():
                image = images.pop()
                x,y,w,h = [int(i) for i in section.area.split(',')]
                fn = resize(image, (w-x, h-y))
                template


        elif isinstance(msg, dict):
            pass

        else:
            raise ValueError
