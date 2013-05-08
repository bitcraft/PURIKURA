"""
*
*   copyright: 2012 Leif Theden <leif.theden@gmail.com>
*   license: GPL-3
*
*   This file is part of pyrikura/purikura.
*
*   pyrikura is free software: you can redistribute it and/or modify
*   it under the terms of the GNU General Public License as published by
*   the Free Software Foundation, either version 3 of the License, or
*   (at your option) any later version.
*
*   pyrikura is distributed in the hope that it will be useful,
*   but WITHOUT ANY WARRANTY; without even the implied warranty of
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*   GNU General Public License for more details.
*
*   You should have received a copy of the GNU General Public License
*   along with pyrikura.  If not, see <http://www.gnu.org/licenses/>.
*
"""

"""
display the camera's live preview using pyglet.

somewhat faster performace that the pygame version, uses a background process
to format the live feed.
"""

import piggyphoto
import pyglet
import os
import time
import ctypes
from PIL import Image
from StringIO import StringIO
from multiprocessing import Process, Queue, Lock, Value
from Queue import Empty
from heapq import heappush, heappop

from pyglet.gl import *
from pyglet.image import *
from pyglet.image.codecs import *


def CameraFeed(camera, camera_lock, frame_queue, image_queue, size):
    running = True
    while running:
        my_frame = frame_queue.get()
        with camera_lock:
            data = camera.capture_preview().get_data()
        im = Image.open(StringIO(data))
        #im.thumbnail(size, Image.ANTIALIAS)
        #im.thumbnail(size)
        #im = im.crop(crop_dim)
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
        #im = im.transpose(Image.FLIP_LEFT_RIGHT)
        image_queue.put((my_frame, (im.size, im.mode, im.tostring())))

class LiveView(object):
    def __init__(self, camera, size):
        self.camera = camera
        self.size = size
        self.sprite = None
        self.prev_sprite = None
        self.texture_width = 512
        self.texture_height = 512
        self.frame_index = 0

        self.frame_heap = []

        self.current_frame = 0
        self.scale = size[0] / float(self.texture_width)

        self.pool = []
        self.camera_lock = Lock()
        self.frame_queue = Queue()
        self.image_queue = Queue()
        for i in xrange(2):
            p = Process(
                target=CameraFeed,
                args=(
                    self.camera,
                    self.camera_lock,
                    self.frame_queue,
                    self.image_queue,
                    (self.texture_width, self.texture_height)
                )
            )
            p.start()
            self.pool.append(p)

    def update(self, dt):
        self.frame_queue.put(self.frame_index)
        self.frame_index += 1

    def update_preview(self, dt=0):

        # empty the image queue
        while 1:
            try:
                frame = self.image_queue.get(False)
            except Empty:
                break
            else:
                heappush(self.frame_heap, frame)

        # get the image with the lowest frame
        try:
            this_frame = self.frame_heap[0][0]
        except IndexError:
            pass
        else:
            if self.current_frame == this_frame:
                self.current_frame += 1

                if self.sprite:
                    self.sprite.delete()

                value, frame = heappop(self.frame_heap)
                (width, height), mode, data = frame

                image = ImageData(width, height, mode, data)
                self.sprite = pyglet.sprite.Sprite(image)
                #self.sprite.scale = self.scale

    def draw(self):
        if self.sprite:
            self.sprite.draw()


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
    time.sleep(1)
    live_view = LiveView(camera, (640, 480))
    live_view.update(0)
    pyglet.clock.schedule(live_view.update)
    pyglet.clock.schedule_interval(live_view.update_preview, update_interval)
    #pyglet.clock.schedule_interval(capture, 7)
    #pyglet.clock.schedule_interval(begin_live_view, 8)

    window.clear()

    @window.event
    def on_draw():
        window.clear()
        live_view.draw()

    try:
        pyglet.app.run()
    except:
        raise
    finally:
        for p in live_view.pool:
            p.terminate()
