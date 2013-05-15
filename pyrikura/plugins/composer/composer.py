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
            layers.append(ready_queue.get(False))
        except Queue.Empty:
            time.sleep(.1)

    # the base to the image we are producing
    base = Image(width=config['width'],
                 height=config['height'],
                 background=Color(config['background']))

    for image_blob, left, top in layers:
        base.composite(Image(blob=image_blob), left, top)

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

        self.magick_lock = Lock()

    def reset(self):
        """
        template is reloaded each time the template is finished
        creating a composite
        """

        # reread the template
        cfg = ConfigParser.ConfigParser()
        cfg.read(self.template)

        # this will be passed to processors
        self._section_config = []
        config = {}

        # cache the sections for use by the preprocessor
        for section in reversed(sorted(cfg.sections())):
            if not section.lower() == 'general':
                self._section_config.append(dict(cfg.items(section)))

        self._required_images = len(self._section_config)

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

    def process(self, msg, sender):
        self.preprocess(msg)
    
        print len(multiprocessing.active_children())

        # temporary mechanism...
        if len(self._section_config) == 0:
            p_conn, c_conn = Pipe()

            p = Process(
                target = compose,
                args = (c_conn, self.ready_queue, self._required_images,
                        self.config)
            )
            p.start()
            filename = p_conn.recv()
            p.join()
            p_conn.close()

            # make sure are children are really dead
            for p in self._processes:
                p.join()

            self._processes = []
            self.reset()
            self.publish([filename])

    def preprocess(self, filename):
        from wand import image
        image = reload(image)

        """
        start a subprocess to preformat the incoming image
        """
        # create a temporary filename in case the file needs to be written to
        # disk.  this is only the case if a filter is needed during processing
        root, ext = os.path.splitext(filename)
        new_filename = 'temp-{}{}'.format(len(self._section_config), ext)

        # create an in-memory copy of the file
        with image.Image(filename=filename) as temp_image:
            image_blob = temp_image.make_blob()
            
        del temp_image, image

        this_config = self._section_config.pop()
        this_config['filename'] = new_filename

        # add this image to the raw_queue
        self.raw_queue.put((image_blob, this_config))

        # spawn another process for processing the image
        # normally, there will be only one active, but may be more
        # if the system is slow or busy
        p = Process(
            target = process_image,
            args = (self.magick_lock, self.raw_queue, self.ready_queue, self.config)
        )
        self._processes.append(p)
        p.start()


class Composer(Plugin):
    _decendant = ComposerBroker
