#!/usr/bin/env python

import glob


#!/usr/bin/env python

import os, glob, subprocess, time
import tempfile
import argparse



# give the script friendly argument procesing
parser = argparse.ArgumentParser()
parser.add_argument('event',
                    help='name of event being managed',
                    type=str)

parser.add_argument("--iphoto", 
                    help='specify to import photos directly into iphoto', 
                    action='store_true',
                    default=False)


parser.add_argument('--prints',
                    help='number of prints to be made',
                    type=int,
                    default=0)


parser.add_argument('--keep',
                    help='keep print images',
                    action='store_true',
                    default=False)

settings = parser.parse_args()

picturesPath = '/Volumes/Mac2/Users/Leif/Pictures/Eye-Fi/'
gm_binary = '/usr/local/bin/gm'


montageCommand = '{0} montage -geometry 1280x1280+0+-20 -tile 1x4 -borderwidth 40 -bordercolor black'
styleCommand = '{0} convert {1} -modulate 120,75,105 -normalize {2}'
stampCommand = '{0} composite -geometry +0+700 {1} {2} {3}'
padleftCommand = '{0} convert {1} -extent 1550x5280-190 {2}'
jpegifyCommand = '{0} convert {1} {2}'


# returns miffs
def preprocess(images):
    new_names = []
    children = []

    for filename in images:
        new_filename = os.path.splitext(filename)[0] + ".miff"
        new_names.append(new_filename)
        names = (gm_binary, filename, new_filename)
        child = subprocess.Popen(styleCommand.format(*names).split())
        children.append(child)

    while [ child for child in children if child.poll() != 0 ]:
        pass

    return new_names


# return None
def import_to_iphoto(images):
    cmd = ['open', '-a', 'iPhoto']
    cmd.extend(images)
    subprocess.call(cmd)


# return miff
def montage(images):
    path = picturesPath + 'montage.miff'
    cmd = montageCommand.format(gm_binary).split()
    cmd.extend(images)
    cmd.append(path)
    subprocess.call(cmd)
    return path


# return miff
def double(image):
    path = picturesPath + 'double.miff'
    cmd = ['gm', 'montage', '-geometry', '1440x5760+20+0', image, image, path]
    subprocess.call(cmd)
    cmd = ['gm', 'convert', '-trim', path, path]
    subprocess.call(cmd)
    return path


# return miff
def stamp(image):
    path = picturesPath + 'stamped.miff'
    stamp = picturesPath + 'title-left.png'
    cmd = stampCommand.format(gm_binary, stamp, image, path)
    subprocess.call(cmd.split())
    return path


# return miff
def frame(image):
    path = picturesPath + 'framed.miff'
    cmd = 'gm convert -frame 215x0+0+0 -mattecolor white'.split()
    cmd.extend([image, 'framed.miff'])
    subprocess.call(cmd)
    return path


# return jpeg
def jpegify(image):
    new_filename = os.path.splitext(image)[0] + ".jpg"
    cmd = jpegifyCommand.format(gm_binary, image, new_filename)
    subprocess.call(cmd.split())
    return new_filename


# return None
def make_print(image):
    cmd = ['lpr', image]
    subprocess.call(cmd)
    return 


# return miff
def padleft(image):
    path = picturesPath + 'padleft.miff'
    cmd = padleftCommand.format(gm_binary, image, path)
    subprocess.call(cmd.split())
    return path    



if __name__ == '__main__':
    while 1:
        time.sleep(2)
        images = glob.glob('{0}*.JPG'.format(picturesPath))[:4]

        if len(images) == 4:
            print "processing next batch of four pictures..."
            new = preprocess(images)

            for filename in images:
                new_path = picturesPath + "originals/" + os.path.split(filename)[1]
                os.rename(filename, new_path)

            this_montage = montage(new)
            [ os.unlink(i) for i in new ]

            this_pad = padleft(this_montage)
            os.unlink(this_montage)

            this_stamped = stamp(this_pad)
            this_jpeg = jpegify(this_stamped)
            os.unlink(this_pad)

            for i in range(settings.prints):
                make_print(this_jpeg)

            os.unlink(this_stamped)

            if settings.iphoto:
                print "waiting for iphoto to settle..."
                jpegs = [ jpegify(i) for i in new ]
                jpegs.append(this_jpeg)
                import_to_iphoto(jpegs)
                time.sleep(5)
                [ os.unlink(i) for i in jpegs ]

            print "finished, waiting for new pictures"
