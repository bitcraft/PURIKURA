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
import pyglet


platform = pyglet.window.get_platform()
display = platform.get_display("")
screens = display.get_screens()
window = pyglet.window.Window(fullscreen=True, screen=screens[-1])



from pyglet.image import *
from PIL import Image, ImageOps
import random, glob

from multiprocessing import Process, Queue
import subprocess

target_size = (512,512)


def get_files():
    #return glob.glob('/var/lib/iii/0018562a8795/events/expo/originals/*.JPG')
    return glob.glob("/home/mjolnir/events/kali-joshua/thumbnails/*JPG")

def init():
    # disable screen blanking because it causes pyglet to lock
    subprocess.call(['xset', '-dpms'])
    subprocess.call(['xset', 's', 'off'])


def load_resize_and_convert(queue, filename):
    image = Image.open(filename)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image.thumbnail(target_size, Image.ANTIALIAS)
    image = ImageOps.expand(image, border=12, fill=(255,255,255))
    image = image.convert()
    w, h = image.size
    image = ImageData(w, h, image.mode, image.tostring())
    queue.put(image)


class TableclothDisplay(object):
    """
    class for showing images that fall onto a scrolling table cloth
    """
    def __init__(self, window, bkg_image, folder):
        self.background = pyglet.graphics.Batch()

        self.width, self.height = window.get_size()

        image = pyglet.image.load(bkg_image)

        self.bkg0 = pyglet.sprite.Sprite(image,
                                         batch=self.background)
        self.bkg1 = pyglet.sprite.Sprite(image,
                                         batch=self.background)

        scale = self.width / float(self.bkg0.width)
        self.bkg0.scale = scale
        self.bkg1.scale = scale

    def scroll(self, x, y):
        self.bkg0.y += y
        self.bkg0.x += x

        if self.bkg0.y >= self.bkg0.height:
            self.bkg0.y = 0
        if self.bkg0.y + self.bkg0.height <= self.height:
            self.bkg0.y = self.height

        self.bkg1.y = self.bkg0.y - self.bkg0.height


load_queue = Queue()
images = []
image_batch = pyglet.graphics.Batch()
displayed = set()
def new_photo(dt=0):
    filename = 'photo.jpg'
    files = get_files()
    if not files: return
    new = set(files) - displayed
    if new:
        filename = random.choice(list(new))
        displayed.add(filename)
    else:
        filename = random.choice(files)
    p = Process(target=load_resize_and_convert, args=(load_queue, filename))
    p.start()



window_size = window.get_size()
#window_size = (1024, 768)
display = TableclothDisplay(window, 'images/background.jpg', '.')

@window.event
def on_draw():
    #window.clear()
    display.background.draw()
    image_batch.draw()

def scroll(dt):
    display.scroll(0, dt * 20.0)
    
    to_remove = []
    for sprite in images:
        if sprite.y > window_size[1]:
            to_remove.append(sprite)

    for sprite in to_remove:
        images.remove(sprite)
        sprite.delete()

    dist = dt * 60.0
    for sprite in images:
        sprite.y += dist

side = 0
def check_queue(dt):
    global side
    try:
        image = load_queue.get(False)
    except:
        pass
    else:
        if side:
            side = 0
            print window_size, image.width, image.height
            x = random.randint(0, window_size[0]/2-image.width)
        else:
            side = 1
            print window_size, image.width, image.height
            x = random.randint(window_size[0]/2, window_size[0]-image.width)

        y = -image.height
        sprite = pyglet.sprite.Sprite(image, x=x, y=y,
                 batch=image_batch)
        images.append(sprite)

if __name__ == '__main__':
    init()

    #pyglet.clock.set_fps_limit(60)
    pyglet.clock.schedule(scroll)
    pyglet.clock.schedule_interval(new_photo, 4)
    pyglet.clock.schedule(check_queue)

    new_photo()
    pyglet.app.run()

