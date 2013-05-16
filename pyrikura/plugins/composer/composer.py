from pyrikura.plugin import Plugin
from pyrikura.broker import Broker
from multiprocessing import Queue, JoinableQueue, Process, Lock, Pipe
import multiprocessing
import logging
import sys
import os
import ConfigParser
import math
import shutil
import time
import subprocess


# mangle import paths to enable this sweet hack
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from filters import *
from imageprocessor import *



# stupid hack to work around stale references in Wand :/
def compose(conn, ready_queue, images, config):
    from wand.image import Image
    from wand.color import Color
    import os

    # get all the images and overlay them
    layers = []
    while len(layers) < images:
        try:
            layer = ready_queue.get()
            layers.append((layer[0]['name'], layer))
        except Queue.Empty:
            time.sleep(.1)

    # the base to the image we are producing
    base = Image(width=config['width'],
                 height=config['height'],
                 background=Color(config['background']))

    for name, (image_config, left, top) in sorted(layers):
        with Image(filename=image_config['filename']) as temp_image:
            base.composite(temp_image, left, top)
        del temp_image

    # save it!
    new_path = 'composite.png'

    # append a dash and numberal if there is a duplicate
    if os.path.exists(new_path):
        i = 1
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


class ComposerBroker(Broker):
    """
    uses templates and images to create print layouts
    """

    def __init__(self, **kwargs):
        super(ComposerBroker, self).__init__(**kwargs)
        self.template = kwargs['template']
        self._processes = []
        self.raw_queue = JoinableQueue()
        self.ready_queue = JoinableQueue()
        self.reset()


    def reset(self):
        """
        template is reloaded each time the template is finished
        creating a composite
        """

        # reread the template
        cfg = ConfigParser.ConfigParser()
        cfg.read(self.template)

        # this will be passed to processors
        self._config_queue = []
        config = {}

        # cache the sections for use by the preprocessor
        self._required_images = 0
        self._total_images = 0
        static_images = []
        for section in reversed(sorted(cfg.sections())):
            if not section.lower() == 'general':
                this_config = dict(cfg.items(section))
                this_config['name'] = section
                self._total_images += 1

                if cfg.get(section, 'filename').lower() == 'auto':
                    self._config_queue.append(this_config)
                    self._required_images += 1
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
            config['width'], config['height'] = [ int(i) for i in s ]
        elif config['units'] == 'inches':
            config['width'], config['height'] = [ int(float(i) * config['dpi']) for i in s ]
      
        # get the background color
        try:
            config['background'] = cfg.get('general', 'background')
        except:
            config['background'] = 'white'

        self.config = config

        for this_config in static_images:
            self.preprocess(this_config)

        self._p_conn, c_conn = Pipe()
        self._composer_process =  Process(
                target = compose,
                args = (c_conn, self.ready_queue, self._total_images,
                        self.config)
        )
        self._composer_process.start()


    def process(self, msg, sender):
        config = self._config_queue.pop()
        config['filename'] = msg
        self.preprocess(config)

        if len(self._config_queue) == 0:
            filename = self._p_conn.recv()
            self._composer_process.join()

            # make sure are children are really dead
            for p in self._processes:
                p.join()

            self._processes = []
            self._composer_process = None
            self.reset()
            self.publish([filename])

    def preprocess(self, config):
        from wand.image import Image
        """
        start a subprocess to preformat the incoming image
        """
        # create a temporary filename in case the file needs to be written to
        # disk.  this is only the case if a filter is needed during processing
      
        filename = config['filename']

        root, ext = os.path.splitext(filename)
        new_filename = 'temp-{}{}'.format(len(self._config_queue), ext)
        config['filename'] = new_filename

        # create a copy of the file
        shutil.copy(filename, new_filename)

        # add this image to the raw_queue
        self.raw_queue.put(config)

        # spawn another process for processing the image
        # normally, there will be only one active, but may be more
        # if the system is slow or busy
        p = Process(
            target = process_image,
            args = (self.raw_queue, self.ready_queue, self.config)
        )
        p.start()
        self._processes.append(p)

class Composer(Plugin):
    _decendant = ComposerBroker
