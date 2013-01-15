"""
program that makes a silly horror movie effect when live-previewing a camera.

this is a failed attempt to use background processes to process the live feed,
but the images were coming back out-of-order, creating this strange effect.

i liked it enough to keep it.
"""

import piggyphoto
import pyglet
import os
import time
from PIL import Image
from StringIO import StringIO
from multiprocessing import Process, Queue, Lock

from pyglet.gl import *
from pyglet.image import *
from pyglet.image.codecs import *


def CameraFeed(camera, lock, queue, size):
    running = True
    while running:
        lock.acquire()
        data = camera.capture_preview().get_data()
        lock.release()
        im = Image.open(StringIO(data))
        #im.thumbnail(size, Image.ANTIALIAS)
        #im.thumbnail(size)
        #im = im.crop(crop_dim)
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
        queue.put((im.size, im.mode, im.tostring()))


class LiveView(object):
    def __init__(self, camera, size):
        self.camera = camera
        self.size = size
        self.sprite = None
        self.prev_sprite = None
        self.texture_width = 512
        self.texture_height = 512

        self.pool = []
        self.lock = Lock()
        self.frame_queue = Queue()
        for i in xrange(4):
            p = Process(
                target=CameraFeed,
                args=(
                    self.camera,
                    self.lock,
                    self.frame_queue,
                    (512,512)
                )
            )
            p.start()
            self.pool.append(p)

    def update(self, dt):
        self.update_preview()

    def update_preview(self):
        if self.sprite != None:
            #self.prev_sprite.delete()
            #self.prev_sprite = sprite
            self.sprite.delete()

        (width, height), mode, data = self.frame_queue.get()
        image = ImageData(width, height, mode, data)
        self.sprite = pyglet.sprite.Sprite(image)

    def draw(self):
        self.sprite.draw()
        #self.prev_sprite.opactiy = 100
        #self.prev_sprite.draw()

update_interval = 1./60
preview_size = (640,480)

w, h = preview_size
minimum, maximum = min(preview_size), max(preview_size)
crop_dim = (((maximum - minimum)/2), 0,
            maximum - ((maximum - minimum)/2), minimum)

window = pyglet.window.Window(fullscreen=True)

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
    for p in live_view.pool:
        p.terminate()
