"""
requires pyserial
"""

import serial



# protocol
trigger_command = 1
shutter_command = 2

# arduino control
arduinoPortNumber = 6

# photo taking preferences
total_pictures = 4
shutter_delay = 5000    # delay between photos
trigger_delay = 3000    # delay before 1st photo after trigger

# misc.
current_picture = 99    # don't change this


def loop():
    while 1: 

        # if is data is ready
        byte = arduinoPort.read(1)
        if byte == trigger_command:
            print 'received trigger!'
            if not trigger:
                trigger = True
                last_trigger_time = time.time()
                beep.play()
                # clear screen, write 'get ready'
            
        if trigger:
            if (time.time() - last_trigger_time) > trigger_delay:
                trigger = False
                processed = False
                current_picture = 0

        if (time.time() - last_shutter_time) > shutter_delay:
            if current_picture < total_pictures:
                current_picture += 1
                last_shutter_time = time.time()
                arduino_port.write(shutter_command)
                # clear the background
                # write the current picture number

        elif current_picture == total_pictures:
            if not processed:
                processed = True
                # launch the image processor
                # update the screen


if __name__ == '__main__':
    arduinoPort = serial.Serial(arduinoPortNumber)

    try:
        loop()
    except:
        raise
