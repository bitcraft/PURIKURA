import pyglet
from pyglet.image import *
from PIL import Image, ImageOps
import random, glob

from multiprocessing import Process, Queue

target_size = (512,512)


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
    files = glob.glob('/var/lib/iii/0018562a8795/events/expo/originals/*.JPG')
    if not files: return
    new = set(files) - displayed
    if new:
        filename = random.choice(list(new))
        displayed.add(filename)
    else:
        filename = random.choice(files)
    p = Process(target=load_resize_and_convert, args=(load_queue, filename))
    p.start()

window = pyglet.window.Window(fullscreen=True)
window_size = window.get_size()
#window_size = (1024, 768)
display = TableclothDisplay(window, 'background.jpg', '.')

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

#pyglet.clock.set_fps_limit(60)
pyglet.clock.schedule(scroll)
pyglet.clock.schedule_interval(new_photo, 4)
pyglet.clock.schedule(check_queue)

new_photo()
pyglet.app.run()
