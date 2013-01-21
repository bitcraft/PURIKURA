"""
templating with pgmagick
"""

from pubsub import pubsub
import sys, os, subprocess, ConfigParser
from pgmagick import Image, Color, Geometry, CompositeOperator as co



class Template(pubsub):
    """
    uses templates and images to create print layouts
    """

    def __init__(self, template):
        super(Template, self).__init__()
        self.template = template
        self.reset()

    def reset(self):
        self._queue = {}
        self._config = ConfigParser.ConfigParser()
        self._config.read(self.template)

        self._mapping = {}
        self._filenames = set()
        self._needed = 0

        # cache the filenames
        for s in self._config.sections():
            for k, v in self._config.items(s):
                #if k.lower() == 'filename' and not v.lower() == 'auto':
                if k.lower() == 'filename':
                    self._mapping[s] = v
                    if v.lower() == 'auto':
                        self._needed += 1

    def process(self, msg, sender):
        self._filenames.add(msg)

        if len(self._filenames) == self._needed:
            self.compose_image()
            self.reset()

    def compose_image(self):
        all_sections = sorted(self._config.sections())
        all_names = list(self._filenames)
        cfg = self._config

        # we are not worried about the general section
        all_sections.remove('general')

        try:
            units = cfg.get('general', 'units').lower()
        except:
            units = 'pixels'

        try:
            dpi = float(cfg.get('general', 'dpi'))
        except:
            dpi = 1.0

        # check if units are inches and raise error if no dpi
        if units == 'inches' and not dpi:
            raise ValueError

        s = cfg.get('general', 'size').split(',') 
        if units == 'pixels':
            s = [ int(i) for i in s ]
        else:
            s = [ int(float(i) * dpi) for i in s ]

        base = Image(Geometry(*s), Color('white'))

        for section in all_sections:
            options = dict(cfg.items(section))

            # attempt to get the area for the image for this section
            try:
                area = options['area'].split(',')
            except KeyError:
                continue

            fn = self._mapping[section]
            if fn.lower() == 'auto':
                fn = all_names.pop()
            else:
                fn = os.path.join('templates', fn)

            if units == 'pixels':
                x,y,x2,y2 = [ int(i) for i in area ] 
            else:
                x,y,x2,y2 = [ int(float(i) * dpi) for i in area ]

            w = x2 - x
            h = y2 - y

            try:
                im = Image(fn)
            except RuntimeError:
                raise Exception, 'could not open file: {0}'.format(fn)

            scale = options.get('scale', None)
            if scale:
                if not scale.lower() == 'false':
                    im.scale('{0}x{1}'.format(w, h))
            else:
                im.scale('{0}x{1}'.format(w, h))

            base.composite(im, x, y, co.OverCompositeOp)

            del im

        new_fn = 'composite.png'
        base.write(new_fn)
        self.publish([new_fn])
