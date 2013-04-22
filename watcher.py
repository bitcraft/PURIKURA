from pyrikura.watcher import Watcher
from pyrikura.template import Template
from pyrikura.consoleprinter import ConsolePrinter
from pyrikura.printer import Printer
from pyrikura.deleter import Deleter
import time, re


eyefi_incoming = '/home/mjolnir/Downloads'


if __name__ == '__main__':
    # create watch for the eye-fi folder
    eyefi = Watcher(eyefi_incoming, re.compile('.*\.jpg$', re.I))

    # create the templater
    template = Template('templates/polaroid0.template')

    # create a simple stdout printer
    output = ConsolePrinter()
   
    # create printer
    printer = Printer()

    # create file eraser
    deleter = Deleter()

    # get output from the watchers
    output.subscribe(eyefi)
    template.subscribe(eyefi)

    # make prints from the templater
    printer.subscribe(template)

    # erase temporary images after the print is spooled
    #deleter.subscribe(printer)

    # loop forever
    while 1:
        time.sleep(1)
        eyefi.tick()
