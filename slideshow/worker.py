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


def thumbnailer(queue, settings):
    from pyglet.image import ImageData
    from PIL import Image, ImageOps
    import random, glob

    displayed = set()

    while 1:
        files = glob.glob("{}/*jpg".format(settings['folder']))
        if not files: raise ValueError

        new = set(files) - displayed
        if new:
            filename = random.choice(list(new))
            displayed.add(filename)
        else:
            filename = random.choice(files)

        image = Image.open(filename)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.thumbnail(settings['thumbnail_size'], Image.ANTIALIAS)
        image = ImageOps.expand(image, border=12, fill=(255,255,255))

        w, h = image.size
        image = image.convert()
        image = ImageData(w, h, image.mode, image.tostring())
        queue.put(image)


def loader(queue, settings):
    from pyglet.image import ImageData
    from PIL import Image, ImageOps
    import random, glob

    displayed = set()

    while 1:
        files = glob.glob("{}/*jpg".format(settings['folder']))
        if not files: raise ValueError

        new = set(files) - displayed
        if new:
            filename = random.choice(list(new))
            displayed.add(filename)
        else:
            filename = random.choice(files)

        image = Image.open(filename)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.thumbnail((1024, 1024), Image.ANTIALIAS)
        image = ImageOps.expand(image, border=32, fill=(255,255,255))

        w, h = image.size
        image = image.convert()
        image = ImageData(w, h, image.mode, image.tostring())
        queue.put(image)
