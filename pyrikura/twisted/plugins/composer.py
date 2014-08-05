from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import reactor, defer
from six.moves import configparser, queue
from pyrikura import ipyrikura

import os
import shutil


class ComposerFactory(object):
    implements(IPlugin)

    def new(self, *args, **kwargs):
        return Composer(*args, **kwargs)


class Composer(object):
    """
    uses templates and images to create print layouts
    """
    implements(ipyrikura.IFileOp)

    def __init__(self, template, **kwargs):
        self.template = template
        self.queue = defer.DeferredQueue()
        self._config_queue = queue.Queue

    def compose(conn, ready_queue, images, config):
        """
        superimpose the layers together
        """
        # hack to work around stale references in Wand
        from wand.image import Image
        from wand.color import Color

        # get all the images and overlay them
        layers = []
        while len(layers) < images:
            try:
                this_config = ready_queue.get()
                layers.append((this_config['name'], this_config))
            except queue.Empty:
                pass

        # the base to the image we are producing
        base = Image(width=config['width'],
                     height=config['height'],
                     background=Color(config['background']))

        cache = {}

        for name, image_config in sorted(layers):
            x, y, w, h = image_config['area']
            try:
                temp_image = cache[image_config['filename']]
            except KeyError:
                temp_image = Image(filename=image_config['filename'])
                cache[image_config['filename']] = temp_image
            base.composite(temp_image, x, y)

        new_path = 'composite.png'
        overwrite = True

        for image in cache.values():
            image.close()

        if not overwrite:
            # append a dash and numeral if there is a duplicate
            if os.path.exists(new_path):
                i = 0
                root, ext = os.path.splitext(new_path)
                new_path = "{0}-{1:04d}{2}".format(root, i, ext)
                while os.path.exists(new_path):
                    i += 1
                    new_path = "{0}-{1:04d}{2}".format(root, i, ext)

        base.format = 'png'
        base.save(filename=new_path)
        base.close()
        conn.send(new_path)
        conn.close()

    def reset(self):
        # reread the template
        cfg = configparser.ConfigParser()
        cfg.read(self.template)

        # this will be passed to processors
        self._config_queue = []
        config = {}

        # cache the sections for use by the preprocessor
        self._total_images = 0
        static_images = []
        for section in reversed(sorted(cfg.sections())):
            if not section.lower() == 'general':
                this_config = dict(cfg.items(section))
                this_config['name'] = section
                areas = [i for i in this_config.keys() if
                         i.lower()[:4] == 'area']
                pos = [i for i in this_config.keys() if
                       i.lower()[:8] == 'position']
                self._total_images += len(areas)
                self._total_images += len(pos)

                if cfg.get(section, 'filename').lower() == 'auto':
                    self._config_queue.append(this_config)
                else:
                    static_images.append(this_config)

        # determine if template is using pixels or inches (dpi)
        try:
            config['units'] = cfg.get('general', 'units').lower()
        except:
            config['units'] = 'pixels'

        try:
            config['dpi'] = float(cfg.get('general', 'dpi'))
        except:
            config['dpi'] = 1.0

        # get size of final image
        s = cfg.get('general', 'size').split(',')

        if config['units'] == 'pixels':
            config['width'], config['height'] = [int(i) for i in s]
        elif config['units'] == 'inches':
            config['width'], config['height'] = [int(float(i) * config['dpi'])
                                                 for i in s]

        # get the background color
        try:
            config['background'] = cfg.get('general', 'background')
        except:
            config['background'] = 'white'

        self.config = config

        for this_config in static_images:
            self.preprocess(this_config)

        self._p_conn, c_conn = Pipe()
        self._composer_process = Process(
            target=compose,
            args=(c_conn, self.ready_queue, self._total_images,
                  self.config)
        )
        self._composer_process.start()

    def process(self, msg, sender=None):
        def compose():
            config = self._config_queue.pop()
            config['filename'] = msg
            self.preprocess(config)



        d = defer.Deferred()
        d.addCallback(compose)
        return d


factory = ComposerFactory()
