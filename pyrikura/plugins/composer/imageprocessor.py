"""
code for unmanaged subprocess that preprocesses images for templates
"""
import Queue, sys, os, time

# mangle import paths to enable this sweet hack
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from filters import *


def process_image(raw_queue, ready_queue, global_config):
    from wand.image import Image

    # get an image from the queue
    try:
        image_config = raw_queue.get()
    except Queue.Empty:
        return

    image = Image(filename=image_config['filename'])

    # attempt to get the area for the image for this section
    try:
        area = image_config['area'].split(',')
    except KeyError:
        x, y = [ int(i) for i in image_config['position'].split(',') ]
        w, h = image.size

    else:
        # calculate the pixel size of this image
        if global_config['units'] == 'pixels':
            x,y,w,h = [ int(i) for i in area ] 
        else:
            x,y,w,h = [ int(float(i) * global_config['dpi']) for i in area ]


    # A U T O C R O P
    autocrop = image_config.get('autocrop', None)
    if autocrop:
        r0 = float(w) / h
        r1 = float(image.width) / image.height

        if r1 > r0:
            scale = float(h) / image.height
            sw = int(image.width * scale)
            cx = int((sw - w)  / 2)
            image.resize(sw, h)
            image.crop(left=cx, width=sw, height=h)


    # S C A L E
    scale = image_config.get('scale', None)
    if scale:
        image.resize(w, h)


    # F I L T E R S
    """
    filters make heavy use of subprocess, so we need to make a temporary file
    for it to manipulate.
    """
    filter = image_config.get('filter', None)
    if filter:
        scratch = 'prefilter-{}.miff'.format(image_config['filename'])
        image.filename = image_config['filename']
        image.format = os.path.splitext(scratch)[1][1:]
        image.save(filename=scratch)
        image.close()
        image = None

        if filter.lower() == 'toaster':
            scratch = toaster(scratch, sw, h)

        # create a new Image object for the queue
        with Image(filename=scratch) as temp_image:
            image = Image(image=temp_image)
        del temp_image

        # delete our temporary image file
        os.unlink(scratch)

    image.format = 'png'
    image.save(filename=image_config['filename'])
    image.close()
    
    ready_queue.put((image_config, x, y))
    ready_queue.close()

    raw_queue.task_done()
