PYRIKURA
========

PYRIKURA is a set of hardware and software plans for a wedding/event photo booth.

It includes image processing, camera control, live slideshow, and touch based
image browser for kiosk operation.

A subset of this project called pyrikura is included in this repository.
Pyrikura automates image processing, camera control, printing, internet
uploading and more.

I use PURIKURA for my professional photobooth service.


Modes of Operation
------------------

PYRIKURA supports many modes of operation and is very flexible.

Many dSLR and consumer cameras are supported.  Eye-fi cameras are supported
with addition software, such as iii.

The software supports multiple screens and cameras.  Both modes can be run at
once.  In many events, I have operated a tethered Canon Rebel XS and a remote
Panasonic Lumix GF-1.

Multiple cameras can be made remote camera and be used together.


Cameras
-------

Any camera supported by libgphoto2 is supported by this software.  An up-to-date
list is available on their website.  Live-view is functional, and can be used
to preview photos before they are taken.

http://www.gphoto.org/proj/libgphoto2/support.php

Webcams are not supported at this time.


Interaction
-----------

PURIKURA supports the arduino for interfacing with physical buttons over USB
and also has a smartphone-inspired touch interface.

The touch interface offers print/reprint controls, viewing, and email.


Running the touch interface
---------------------------

Check out the software and hardware requirements first.  You can use the
supplied script 'run.sh' to get started.  Please let me know if you have any
issues.


Slideshow
---------

A simple slideshow is included that will automatically add new images from a
hot folder.  There are currently 3 formats that rotate: a ken burns effect, a
stacked photos effect, and simple scrolling photos effect.


Getting Help
------------

If you encounter any errors, please issue a bug report.  Also, please note that
while I am providing the software for free, my time is not free.  If you wish to
use this software and need help getting you system going I will be accepting
paypal donations in exchange for my time.

I reserve all rights to determine what features will be added and how the
interface is used for this software that is hosted here.  You are welcome to
fork this project at any time and customize it as you wish.


Why is it free?
---------------

Information wants to be free.  Donations are accepted and appreciated.


The Name
--------

'purukura' is a term used in Japan for their ubiquitous style of photo booths.


Requirements
------------

This is a general list of software requirements.  Certain functions of this
software may require additional dependancies.

-  Debian Linux or OS X 10.x
-  Python 2.7
-  Twisted
-  shutter
-  PyGame
-  libgphoto


All files under the 'pyrikura' directory are copyright Leif Theden, 2012-2014
and licensed under the GPLv3.

All other code may or not be GPLv3, please check the source of each file.
