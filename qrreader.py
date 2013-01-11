import piggyphoto
import pyglet
import os
import time
from PIL import Image
from StringIO import StringIO
from multiprocessing import Process, Queue

from pyglet.gl import *
from pyglet.image import *
from pyglet.image.codecs import *

import zbar


class LiveView(object):
    def __init__(self, camera, size):
        self.camera = camera
        self.size = size
        self.frame_queue = Queue()
        self.image = None
        self.sprite = None
        self.size_internal = (512, 512)
        self.scanner = zbar.ImageScanner()

    def update(self, dt):
        self.capture_preview()

    def capture_preview(self):
        if self.sprite != None:
            self.sprite.delete()

        data = self.camera.capture_preview().get_data()
        im = Image.open(StringIO(data)).convert('L')
        width, height = im.size
        image = zbar.Image(width, height, 'Y800', im.tostring())
        self.scanner.scan(image)

        for symbol in image:
            print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data

    def draw(self):
        pass

update_interval = 1./60
preview_size = (640,480)

w, h = preview_size
minimum, maximum = min(preview_size), max(preview_size)
crop_dim = (((maximum - minimum)/2), 0,
            maximum - ((maximum - minimum)/2), minimum)

window = pyglet.window.Window()
#window = pyglet.window.Window(fullscreen=True)

if __name__ == '__main__':
    camera = piggyphoto.camera()
    camera.leave_locked()
    live_view = LiveView(camera, (640, 480))
    live_view.update(0)
    pyglet.clock.schedule_interval(live_view.update, update_interval)
    #pyglet.clock.schedule_interval(capture, 7)
    #pyglet.clock.schedule_interval(begin_live_view, 8)

    @window.event
    def on_draw():
        window.clear()
        live_view.draw()

    pyglet.app.run()
