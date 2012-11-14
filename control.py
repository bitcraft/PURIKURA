"""
requires pyserial, pygame, graphicsmagick

control program for the photo booth

it is recommended that the script be executed in a ramdisk

used in tandem with an arduino connected via psuedo serial on usb
implements simple protocol for controlling the camera
"""

import serial
import argparse
import subprocess
import os


parser = argparse.ArgumentParser()

parser.add_argument('event',
                    help='name of event being managed',
                    type=str)

parser.add_argument('--prints',
                    help='number of prints to be made',
                    type=int,
                    default=0)

parser.add_argument('--sound',
                    help='filename of sound to be played after trigger',
                    type=string,
                    default=os.path.join('sounds', 'beep.wav')

settings = parser.parse_args()


# external commands for image manipulation
montageCommand = '{0} montage -geometry 1280x1280+0+-20 -tile 1x4 -borderwidth 40 -bordercolor black'
styleCommand = '{0} convert {1} -modulate 120,75,105 -normalize {2}'
stampCommand = '{0} composite -geometry +0+700 {1} {2} {3}'
padleftCommand = '{0} convert {1} -extent 1550x5280-190 {2}'
jpegifyCommand = '{0} convert {1} {2}'


picturesPath = '/Volumes/Mac2/Users/Leif/Pictures/Eye-Fi/'
gm_binary = '/usr/local/bin/gm'


# protocol
trigger_command = 1         # when button is pressed to start picture seq.
shutter_command = 2         # command to cause camera shutter
inc_print_command = 3       # when more prints are needed
dec_print_command = 4       # when less prints are needed
reprint_command = 5         # when another print is needed from last event
reset_command = 6           # when photos are out of sequence
set_busy = 7                # when camera is actively taking photos
set_not_busy = 8            # when camera is no longer taking pictures

# arduino control
arduinoPortNumber = 6

# photo taking preferences
total_pictures = 4
shutter_delay = 5000    # delay between photos
trigger_delay = 3000    # delay before 1st photo after trigger

# misc.
current_picture = 9999  # don't change this


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


# return miff
def montage(images, dest):
    cmd = montageCommand.format(gm_binary).split()
    cmd.extend(images)
    cmd.append(dest)
    subprocess.call(cmd)
    return dest


# return miff
def padleft(image):
    path = os.path.join('padleft.miff')
    cmd = padleftCommand.format(gm_binary, image, path)
    subprocess.call(cmd.split())
    return path


# return miff
def stamp(image, stamp, dest):
    cmd = stampCommand.format(gm_binary, stamp, image, dest)
    subprocess.call(cmd.split())
    return dest


# return jpeg
def jpegify(image):
    path = os.path.splitext(image)[0] + ".jpg"
    cmd = jpegifyCommand.format(gm_binary, image, path)
    subprocess.call(cmd.split())
    return path


# return None
# tested on os x
def make_print(image):
    cmd = ['lpr', image]
    subprocess.call(cmd)
    return 


def make_composite(images, title):
    """
    produces a 2x6 photo strip with an image-title on the left
    returns the filename of the image
    """

    this_montage = montage(images, 'montage.miff')
    [ os.unlink(i) for i in images ]

    this_pad = padleft(this_montage)
    os.unlink(this_montage)

    stamp_name = os.path.join('events', settings.event, title)
    this_stamped = stamp(this_pad, stamp_name, 'stamped.miff')
    this_jpeg = jpegify(this_stamped)
    os.unlink(this_stamped)
    os.unlink(this_pad)

    return this_jpeg


def monitor(path, serial_port):
    import pygame

    beep = pygame.mixer.Sound(settings.sound_file)

    os.chdir(path)

    last_trigger_time = 0.0


    while 1: 
        time.sleep(0.5)

        # check our serial port for an incoming command
        byte = serial_port.read(1)

        if byte == trigger_command:
            if not trigger:
                trigger = True
                last_trigger_time = time.time()
                beep.play()

        elif byte == inc_print_command:
            settings.prints += 1

        elif byte == dec_print_command:
            settings.prints -= 1

        elif byte == reset_command:
            jpegs = glob.glob('*.JPG')
            for filename in jpegs:
                new_path = os.path.join('events', settings.event, 'lost')
                os.rename(filename, os.path.join(new_path, filename))

        elif byte == reprint_command:
            make_print('stamped.jpg')


        # trigger is true if camera is taking photos
        if trigger:
            jpegs = glob.glob('*.JPG')

            if jpegs:
                preprocess(jpegs)

                # move the jpegs into the originals folder
                for filename in jpegs:
                    new_path = os.path.join('events', settings.event, 'originals')
                    os.rename(filename, os.path.join(new_path, filename))

            if (time.time() - last_trigger_time) > trigger_delay:
                current_picture = 0

            if (time.time() - last_shutter_time) > shutter_delay:
                if current_picture < total_pictures:
                    current_picture += 1
                    last_shutter_time = time.time()
                    serial_port.write(shutter_command)

                elif current_picture == total_pictures:
                    trigger = False

        else:
            # check for preprocessed images (miff)
            miffs = glob.glob('*.miff')[:4]

            # we have enough preprocessed images to make a photo strip
            if len(miffs) == 4:
                image = make_composite(miffs)
                
                for i in range(settings.prints):
                    make_print(image)


if __name__ == '__main__':
    arduinoPort = serial.Serial(arduinoPortNumber)
    monitor(picturesPath, arduinoPort)
