import pyglet
from pyglet.image import *
from PIL import Image



class TableclothDisplay(object):
    """
    class for showing images that fall onto a scrolling table cloth
    """
    def __init__(self, window, bkg_image, folder):
        self.background = pyglet.graphics.Batch()

        self.width, self.height = window.get_size()

        image = pyglet.image.load(bkg_image)

        self.bkg0 = pyglet.sprite.Sprite(image, batch=self.background)
        self.bkg1 = pyglet.sprite.Sprite(image, batch=self.background)

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


def new_photo(filename):
    sprite = pyglet.sprite.Sprite(filename)

window = pyglet.window.Window(fullscreen=True)
display = TableclothDisplay(window, 'background.jpg', '.')

@window.event
def on_draw():
    window.clear()
    display.background.draw()

def scroll(dt):
    display.scroll(0, dt * 60.0)

pyglet.clock.set_fps_limit(60)
pyglet.clock.schedule(scroll)

pyglet.app.run()
