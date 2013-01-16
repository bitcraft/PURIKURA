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
This file contains a few functions that can be used to process your images.
"""

import glob
from wand.image import Image, Color


def make2x6(images):
    """
    create a 2x6 photo trip with 4 photos and a banner on the left side
    expects list of wand Images.
    """
    if not len(images) == 4:
        raise ValueError, 'Must supply exactly 4 images to make strip'

    dpi = 1440
    border_width = 40
    border_color = Color('#000000')
    background_color = Color('#FFFFFF')

    strip_size = 2 * dpi, 6 * dpi
    s = int((strip_size[1]+(3*border_width))/4.0)
    target_size = s-border_width*2, s-border_width*2
    x_off, y_off = strip_size[0] - s - (border_width * 4), 0

    # convert to integers
    strip_size = int(strip_size[0]), int(strip_size[1])

    # generate the blank image
    background = Image(width=strip_size[0],
                       height=strip_size[1],
                       background=background_color)
    
    padding = 0, s

    # compose the strip
    for im in images:
        im.resize(*target_size)
        background.composite(im, x_off, y_off)
        x_off += padding[0]
        y_off += padding[1]

    return background


def square_crop(image):
    """
    Chop the sides off an image to make it square.
    expects a single wand Image
    """
    # get the size
    w, h = image.size

    if w > h:
        diff = w - h
        box = (diff/2, 0, w-diff/2, h)

    image.crop(*box)

    return image

if __name__ == '__main__':
    # load the images
    images = [ Image(filename=i) for i in glob.glob('*.JPG') ]
    
    # crop the images to make them square
    images = [ square_crop(i) for i in images ]

    im = make2x6(images)
    with open('strip.jpg', 'wb') as fh:
        im.format = 'jpeg'
        im.save(fh)


def overlayPolaroid(image):
    """
    Overlay the 'polaroid' template
    """
    pass


montageCommand = '{0} montage -geometry 1280x1280+0+-20 -tile 1x4 -borderwidth 40 -bordercolor black'
styleCommand = '{0} convert {1} -modulate 120,75,105 -normalize {2}'
stampCommand = '{0} composite -geometry +0+700 {1} {2} {3}'
padleftCommand = '{0} convert {1} -extent 1550x5280-190 {2}'
jpegifyCommand = 'convert {1} {2}'
squarifyCommand = '{0} convert -gravity center -crop {1}x{1}+0+0 +repage -resize 1060x1060 {2} {3}'
polaroidCommand = 'composite -compose Dst_Over -geometry +94+435 {1} {2} {3}'


def polaroid(miff, size, template):
    sq = 'square.tiff'
    cmd = squarifyCommand.format(gm_binary, size, miff, sq).split()
    subprocess.call(cmd)
    filename = 'framed.miff'
    cmd = polaroidCommand.format(gm_binary, sq, template, filename).split()
    subprocess.call(cmd)
    os.unlink(sq)
    return filename

