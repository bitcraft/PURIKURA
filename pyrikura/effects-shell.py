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
#picturesPath = os.path.join(root, 'events', settings.event)


montageCommand = '{0} montage -geometry 1280x1280+0+-20 -tile 1x4 -borderwidth 40 -bordercolor black'
styleCommand = '{0} convert {1} -modulate 120,75,105 -normalize {2}'
stampCommand = '{0} composite -geometry +0+700 {1} {2} {3}'
padleftCommand = '{0} convert {1} -extent 1550x5280-190 {2}'
jpegifyCommand = '{0} convert {1} {2}'


# returns miffs
# launches a separate thread for each photo
def preprocess(images):
    new_names = []
    children = []

    for filename in images:
        new_filename = os.path.splitext(filename)[0] + ".miff"
        new_names.append(new_filename)
        names = (gm_binary, filename, new_filename)
        cmd = styleCommand.format(*names).split()
        child = subprocess.Popen(cmd)
        children.append((child, filename, cmd))

    # wait for all the children to finish
    while any(i for i in children if i[0].poll() is None):
        pass

    # sometimes a JPG is found but not completely written to disk
    # in these cases, gm will fail and return 1
    failed = [ i[1] for i in children if i[0].poll() == 1 ]
    if failed:
        preprocess(failed)

    return new_names


# return None
def import_to_iphoto(images):
    cmd = ['open', '-a', 'iPhoto']
    cmd.extend(images)
    subprocess.call(cmd)


# return miff
def montage(images, dest):
    cmd = montageCommand.format(gm_binary).split()
    cmd.extend(images)
    cmd.append(dest)
    subprocess.call(cmd)
    return dest


# return miff
# broken
def double(image):
    path = picturesPath + 'double.miff'
    cmd = ['gm', 'montage', '-geometry', '1440x5760+20+0', image, image, path]
    subprocess.call(cmd)
    cmd = ['gm', 'convert', '-trim', path, path]
    subprocess.call(cmd)
    return path


# return miff
def stamp(image, stamp, dest):
    cmd = stampCommand.format(gm_binary, stamp, image, dest)
    subprocess.call(cmd.split())
    return dest


# return miff
# broken
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
    current = {}

    print 'starting image processor...'

    os.chdir(picturesPath)
    os.chdir('events')

    # check that the event folder exists and is writable
    ok = False
    if os.path.exists(settings.event):
        os.chdir(settings.event)
        if os.path.exists('title-left.png'):
            ok = True

    if not ok:
        raise Exception, 'missing event directory or title stamp'


    os.chdir(picturesPath)

    print 'all systems go (hopefully)'

    # template is ok, lets start watching for files
    while 1:
        time.sleep(0.5)

        # check for jpegs from the camera
        jpegs = glob.glob('*.JPG')

        # we have some jpegs lets convert them to miffs for processing
        if jpegs:
            preprocess(jpegs)

            # move the jpegs into the originals folder
            for filename in jpegs:
                new_path = os.path.join('events', settings.event, 'originals')
                os.rename(filename, os.path.join(new_path, filename))

        # check for preprocessed images (miff)
        miffs = glob.glob('*.miff')[:4]

        # we have enough preprocessed images to make a photo strip
        if len(miffs) == 4:
            this_montage = montage(miffs, 'montage.miff')
            [ os.unlink(i) for i in miffs ]

            this_pad = padleft(this_montage)
            os.unlink(this_montage)

            stamp_name = os.path.join('events', settings.event, 'title-left.png')
            this_stamped = stamp(this_pad, stamp_name, 'stamped.miff')
            this_jpeg = jpegify(this_stamped)
            os.unlink(this_stamped)
            os.unlink(this_pad)

            # make prints
            for i in range(settings.prints):
                make_print(this_jpeg)

            # iphoto?
            if settings.iphoto:
                print "waiting for iphoto to settle..."
                import_to_iphoto(jpegs)
                time.sleep(5)
