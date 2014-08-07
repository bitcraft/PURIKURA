#!/usr/bin/env python
"""
This program is the nuts and bolts of the photo booth.

It uses a workflow/broker hack to make a photobooth.  In relationship with
the entire project, this is all that is needed to accept input, take photos,
compose and print them.  The kiosk app can be thought of as a pretty
touch-enabled file browser.

This creates all the images that you can browse with in the kiosk app.

This configuration is used in my professional photo booth service and uses an
arduino for input.  Free free to customize.
"""
import sys
sys.path.append('/home/mjolnir/git/PURIKURA/')

import pygame
import logging
import os
import glob

import yapsy
from yapsy.PluginManager import PluginManager
logging.getLogger('yapsy').setLevel(logging.DEBUG)

from pyrikura import resources
from pyrikura.config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.booth")

# because i hate typing
jpath = os.path.join

# paths
app_root_path = Config.get('paths', 'root')
app_config_path = jpath(app_root_path, 'config')
app_resources_path = jpath(app_root_path, 'resources')
app_sounds_path = jpath(app_resources_path, 'sounds')
app_images_path = jpath(app_resources_path, 'images')
all_templates_path = jpath(app_resources_path, 'templates')
all_images_path = Config.get('paths', 'images')
capture_image = Config.get('camera', 'capture-image')
shared_path = Config.get('paths', 'shared')
plugins_path = Config.get('paths', 'plugins')

# event paths
event_name = Config.get('event', 'name')
template_path = jpath(all_templates_path, Config.get('event', 'template'))
event_images_path = jpath(all_images_path, event_name)
thumbs_path = jpath(event_images_path, 'thumbnails')
details_path = jpath(event_images_path, 'detail')
originals_path = jpath(event_images_path, 'originals')
composites_path = jpath(event_images_path, 'composites')
paths = ('thumbnails', 'detail', 'originals', 'composites')

# specific to the camera system i use!
dbus_name = Config.get('camera', 'dbus-name') + '.camera'
dbus_path = Config.get('camera', 'dbus-path') + '/camera'

# load all the stuff
pygame.init()
resources.load()


class Session:
    def __init__(self):
        logger.debug('building new session...')

        def p(name, *arg, **kwarg):
            plugin = pm.getPluginByName(name)
            if not plugin:
                msg = "cannot load plugin {}".format(plugin)
                logger.error(msg)
                raise ValueError
            return plugin.plugin_object.new(*arg, **kwarg)

        pm = PluginManager()
        pm.setPluginPlaces([plugins_path])
        pm.collectPlugins()

        for pi in pm.getAllPlugins():
            pm.activatePluginByName(pi.name)

        comp = p('Composer', template=template_path)
        arch = p('FileCopy', dest=composites_path)

        self.comp = comp
        arch.subscribe(comp)

    def run(self):
        glob_pattern = '*.jpg'
        leading = 'sarah-josh-'
        leading_len = len(leading)

        tmp = [(int(i[leading_len:len(i)-4]), i)
               for i in glob.glob(glob_pattern) if i.startswith(leading)]
        tmp.sort()
        for fn in [i[1] for i in tmp]:
            print fn
            self.comp.process(fn)

        print 'finished'

if __name__ == '__main__':
    logger.debug('starting compositor')
    session = Session()
    session.run()
