from pyrikura import *
import time, re


eyefi_incoming = '/home/iiid/incoming/0018562a8795'
printer_folder = '/home/mjolnir/smb-printsrv/'
printer_folder = '/home/mjolnir/'


if __name__ == '__main__':
    # create watch for the eye-fi folder
    eyefi = Watcher(eyefi_incoming, re.compile('.*\.jpg$', re.I))

    # create the templater
    template = Template('templates/polaroid0.template')

    # create a simple stdout printer
    output = ConsolePrinter()

    # create file mover for printer
    # ( another service is monitoring this folder and will print new files )
    copier = Copier(output=printer_folder)

    # create printer
    #printer = Printer()

    # create file eraser
    #deleter = Deleter()

    # get output from the watchers
    output.subscribe(eyefi)
    template.subscribe(eyefi)

    copier.subscribe(template)

    # make prints from the templater
    #printer.subscribe(template)

    # erase temporary images after the print is spooled
    #deleter.subscribe(printer)

    # loop forever
    while 1:
        time.sleep(.5)
        eyefi.tick()
