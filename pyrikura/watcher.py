#!/usr/bin/env python
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

import os, glob, subprocess, time
import tempfile
import argparse


picturesPath = '/var/lib/iii/0018562a8795'
gm_binary = '/usr/bin/gm'


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
    print ' '.join(cmd)
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



class Watcher(object):
    """
    Class to watch a folder and do photo related stuff to it.
    """

    def __init__(self, options):
        self._options = options

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def tick(self, td=0.0):
        current = {}
        os.chdir(picturesPath)
        polaroid_template = 'templates/polaroid0.png'

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
        for miff in glob.glob('*.miff'):
            print "miffs", miff
            framed = polaroid(miff, 1504, polaroid_template)
            this_jpeg = jpegify(framed)
            os.unlink(framed)
            os.unlink(miff)

            # make prints
            for i in range(settings.prints):
                make_print(this_jpeg)

