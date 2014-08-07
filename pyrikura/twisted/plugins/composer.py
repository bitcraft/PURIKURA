import sys
sys.path.append('/home/mjolnir/git/PURIKURA')

from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import reactor, defer
from six.moves import configparser, queue
from pyrikura import ipyrikura

import os
import shutil


"""
how things generally work:

    the composer reads a template
    generate a new config for each image in the template
    using a pool of subprocesses, let workers process each image
    when all images are finshed layer them and make a final output
"""

class ComposerFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)

    def new(self, *args, **kwargs):
        return Composer(*args, **kwargs)


class Composer(object):
    """
    uses templates and images to create print layouts
    """
    implements(ipyrikura.IFileOp)

    def __init__(self, template, **kwargs):
        self.template = template
        self.finished_layers = queue.Queue()
        self.task_queue = queue.Queue()

        # this will be passed to processors
        config = dict()

        for section in reversed(sorted(cfg.sections())):
            if not section.lower() == 'general':
                new_cfg = dict(cfg.items(section))
                new_cfg['name'] = section
                areas = [i for i in new_cfg.keys() if
                         i.lower()[:4] == 'area']
                pos = [i for i in new_cfg.keys() if
                       i.lower()[:8] == 'position']

                if cfg.get(section, 'filename').lower() == 'auto':
                    self.task_queue.append(new_cfg)
                else:
                    static_images.append(new_cfg)

        config['units'] = cfg.get('general', 'units').lower()
        config['dpi'] = cfg.getfloat('general', 'dpi'))
        config['background'] = cfg.get('general', 'background')

        s = cfg.get('general', 'size').split(',')

        if config['units'] == 'pixels':
            size = [int(i) for i in s]

        elif config['units'] == 'inches':
            size = [int(float(i) * config['dpi']) for i in s]

        else:
            raise ValueError

        config['width'], config['height'] = size

        self.config = config

    def compose(self):
        """
        superimpose the layers together
        """
        # hack to work around stale references in Wand
        from wand.image import Image
        from wand.color import Color

        # layers is a list of (name, config) tuples
        layers = []

        # the base to the image we are producing
        base = Image(width=config['width'],
                     height=config['height'],
                     background=Color(config['background']))

        # some layouts may reference the same image for than twice, for
        # instance, 2x6 stips on a 4x6 image.  the cache prevents the
        # image from wastefullly being loaded more than once.
        cache = {}

        # layers are sorted with the last items 'on top' of the final image
        for name, config in sorted(layers):
            filename = config['filename']
            try:
                image = cache[filename]
            except KeyError:
                image = Image(filename=filename)
                cache[filename] = image
            x, y, w, h = config['area']
            base.composite(image, x, y)

        # the images must be explicitly closed
        for image in cache.values():
            image.close()

        filename = 'composite.png'

        base.format = filename[-3]
        base.save(filename=new_path)
        base.close()

    def process(self, msg, sender=None):
        pass


factory = ComposerFactory()
