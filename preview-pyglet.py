import piggyphoto
import pyglet
import os
import time
from PIL import Image
from StringIO import StringIO

from pyglet.gl import *
from pyglet.image import *
from pyglet.image.codecs import *

update_interval = 1./60
preview_size = (640,480)

w, h = preview_size
minimum, maximum = min(preview_size), max(preview_size)
crop_dim = (((maximum - minimum)/2), 0,
            maximum - ((maximum - minimum)/2), minimum)

window = pyglet.window.Window()

c = piggyphoto.camera()
c.leave_locked()

live_view = True

def capture(dt=0):
    global live_view
    c.capture_image('photo.jpg')
    im = Image.open('photo.jpg')
    im.thumbnail(preview_size)
    im = im.transpose(Image.FLIP_TOP_BOTTOM)
    width, height = im.size
    image = ImageData(width, height, im.mode, im.tostring())
    #window.clear()
    image.blit(0,0)
    live_view = False

def update_preview(dt=0):
    if not live_view: return
    cfile = c.capture_preview()
    data = cfile.get_data()
    im = Image.open(StringIO(data))
    im.thumbnail(preview_size)
    im = im.crop(crop_dim)
    im = im.transpose(Image.FLIP_TOP_BOTTOM)
    width, height = im.size
    image = ImageData(width, height, im.mode, im.tostring())
    #window.clear()
    image.blit(0,0)


def begin_live_view(dt=0):
    global live_view
    live_view = True

pyglet.clock.schedule_interval(update_preview, update_interval)
#pyglet.clock.schedule_interval(capture, 7)
#pyglet.clock.schedule_interval(begin_live_view, 8)

pyglet.app.run()
