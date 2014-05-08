PYRIKURA
========

PYRIKURA is a set of hardware and software plans for a wedding/event photo booth.

It includes image processing, camera control, live slideshow, and touch based
image broswer for kiosk operation.

A subset of this project called pyrikura is included in this repository.
Pyrikura automates image processing, camera control, printing, internet
uploading and more.

I use PURIKURA for my professional photobooth service.


Modes of Operation
------------------

PURIKURA supports many modes of operation and is very flexible.

The workflow/broker system allows almost unlimited customization.
Workflows can be saved and used at a later time.

Many dSLR and comsumer cameras are supported.  Eye-fi cameras are supported
with addition software, such as iii.

The software supports multiple screens and cameras.  Both modes can be run at
once.  In many events, I have operated a tethered Canon Rebel XS and a remote
Panasonic Lumix GF-1.

Multiple cameras can be made remote camera and be used together.


Cameras
-------

Any camera supported by libgphoto2 is supported by this software.  An up-to-date
list is available on their website.  Live-view is functional, but unused at
this time.

http://www.gphoto.org/proj/libgphoto2/support.php

Webcams are not supported.


Interaction
-----------

PURIKURA supports the arduino for interfacing with physical buttons over USB
and also has a smartphone-inspired touch interface.

The touch interface offers print/reprint controls, viewing, and email.


Running the touch interface
---------------------------

Check out the software and hardware requirements first.  You can use the
supplied script 'run.sh' to get started.  Please let me know if you have any
issues!


Slideshow
---------

A simple slideshow is included that will automatically add new images from a
hot folder.  There are currently 3 formats that rotate: a ken burns effect, a
stacked photos effect, and simple scrolling photos effect.


Boring Technical Details
------------------------

The core concept of pyrikura is the *workflow*.  A workflow describes how
images are manipulated.  A workflow is comprised of many different 'brokers'.

Plugins are used to create brokers.  Included broker plugins are:
    - Composer (for templates)
    - Folder Watcher (hot folders)
    - File move and copy
    - Tethered Camera
    - Twitter
    - Arduino
    - Printer

Brokers are connected to each other to create a workflow.  A simple workflow for
a photobooth could be this:

    arduino => camera =============> composer => twitter
                      => file copy            => printer


In words:
    The arduino recieves a trigger to take the picture
    The camera takes one photo sends it to the composer and file copier
        the file copier copies the original file to archive it
        the composer uses a template to add a background
            this modified photo is posted to twitter, printed, and archived



Getting Help
------------

If you encounter any errors, please issue a bug report.  Also, please note that
while I am providing the software for free, my time is not free.  If you wish to
use this software and need help getting you system going I will be accepting
paypal donations in exchange for my time.

I reserve all rights to determine what features will be added and how the
interface is used.  You are welcome to fork this project at any time and
customize it as you wish.


Why is it free?
---------------

Information wants to be free.  Donations are accepted and appreciated.


The Name
--------

'purukura' is a term used in Japan for their ubiquitous style of photo booths.


Software and Hardware Requirements
----------------------------------

-  Debian Linux (Wheezy/Testing just a guideline)
-  Python 2.7
-  libgphoto
-  piggyphoto (included)
-  Pygame (for sound)
-  GraphicsMagick
-  Imagemagick (possibly required...)
-  Twisted

Optional Software/Hardware
--------------------------

-  Pyglet
-  Arduino


All files under the 'pyrikura' directory are copyright Leif Theden, 2012-2014
and licensed under the GPLv3.

All other code may or not be GPLv3, please check the source of each file.