"""
code for unmanaged subprocess that preprocesses images for templates
"""
import Queue
import sys

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
    raw_areas = []
    all_areas = []
    done = []

    temp_areas = [i for i in image_config.keys() if i[:4].lower() == 'area']
    for area in temp_areas:
        area = image_config[area]
        raw_areas.append(tuple([float(i) for i in area.split(',')]))

    temp_positions = [i for i in image_config.keys() if
                      i[:8].lower() == 'position']
    for pos in temp_positions:
        pos = image_config[pos]
        if global_config['units'] == 'pixels':
            x, y = [int(i) for i in pos.split(',')]
            w, h = image.size
        else:
            x, y = [int(int(i) * global_config['dpi']) for i in pos.split(',')]
            w, h = [int(int(i) / global_config['dpi']) for i in image.size]

        this_config = dict(image_config)
        this_config['area'] = (x, y, w, h)
        ready_queue.put(this_config)

        #raw_areas.append((x,y,w,h))

    # REWRITE THIS!
    for area in raw_areas:
        if global_config['units'] == 'pixels':
            x, y, w, h = [int(i) for i in area]
        else:
            x, y, w, h = [int(float((i)) * global_config['dpi']) for i in area]
        all_areas.append((x, y, w, h))

    # process each image
    for x, y, w, h in all_areas:
        if (w, h) not in done:
            # A U T O C R O P
            autocrop = image_config.get('autocrop', None)
            if autocrop:
                r0 = float(w) / h
                r1 = float(image.width) / image.height

                if r1 > r0:
                    scale = float(h) / image.height
                    sw = int(image.width * scale)
                    cx = int((sw - w) / 2)
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

        done.append((w, h))
        this_config = dict(image_config)
        this_config['area'] = (x, y, w, h)
        ready_queue.put(this_config)

    ready_queue.close()
    raw_queue.task_done()
