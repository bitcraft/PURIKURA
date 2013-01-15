PYRIKURA
========

PYRIKURA is a set of hardware and software plans for a DIY wedding/event photo booth.

It is capable of producing excellent looking 2x6 inch color photo strips with 4 square photos or any other design if designed and coded into the script.


Why is it free?
---------------

I've used and worked with photo booth owners in the past and what bothers me the
most about all of it is the lack of time spent on customer interaction and
friendliness.  I understand that photo booths are always changing and oners are
faced with new software and hardware upgrades every year.

All of these changes adds to the bottom line, and sometimes, and operator is
faced with making a decision between providing a fun experience and maintaining
their equipment.

I'm releasing the software that I develop for my own photo booth business free
and open source.  I hope that my project will encourage others to use and
develop on my platform.

With a free software base, I hope that photo booth operators will have more time
to concentrate on their clients and provide a more enjoyable experience for
their clients.

This will also make free operators from costly software licences and let them
customize the experience for each user.


Modes of Operation
------------------

PYRIKURA supports two modes of operation:
    Tethered DSLR (any camera supported by libgphoto)
    Remote Camera via eye-fi X2 SD Card

Tethered mode requires a tripod and a trigger.  I use an arduino to provide a
switch to activate the booth.

Remote camera mode is any camera supporting an SD card.  The camera does not
require any wired connections to the host computer.  All images from the camera
will be automatically uploaded to the host computer.  The range is limited by
the X2 card, about 25ft from experience.

The software supports multiple screens and cameras.  Both modes can be run at
once.  In many events, I have operated a tethered Canon Rebel XS and a remote
Panasonic Lumix GF-1.

Multiple cameras can be made remote camera and be used together.


QR Codes and Social Media
-------------------------

I am experimenting with generating QR codes for images so users and simply scan
the photo to get access to their photos.  From there they will be able to save
the images and upload them to their favorite social media site.


Example Setup
-------------

The arduino is connected to a button and the camera.  The button is a simple microswitch connected to a rope.  The arduino has a simple shield that mimicks a shutter release cable using two relays.

Inside the camera is a Eye-Fi X2 4gb SD card with wifi.  As soon as the picture is taken, the photo is sent to the computer.  The python script continously monitors the incoming photo folder and once there are four new photos on the computer, the script uses GraphicsMagick to compose a print and the resulting image is sent to the printer.


Modifications
-------------

The script is completely open to customization and a few variables can be changed right in the script.  I've chosen to have the photo booth activated with a rope, but you could make it a button, or anything else you desire.


Getting Help
------------

If you encounter any errors, please issue a bug report.  Also, please note that
while I am providing the software for free, my time is not free.  If you wish to
use this software and need help getting you system going I will be accepting
paypal donations in exchange for my time.

I reserve all rights to determine what features will be added and how the
interface is used.  You are welcome to fork this project at any time and
customize it as you wish.


The Name
--------
 
'purukura' is a term used in Japan for their ubiquitous style of photo booths.


Hardware
--------

-  Eye-Fi X2 card (any capacity)
-  Canon Rebel XS
-  Panasonic Lumix GF-1
-  Arduino Uno
-  Epson PictureMate Charm (PM 225)
-  Pentium-class PC



Software
--------

-  Debian Linux (Wheezy/Testing)
-  libgphoto
-  piggyphoto
-  Arduino
-  Python 2.7
-  Pygame (for sound)
-  Pyglet
-  GraphicsMagick
-  pyinotify
-  zbar


Future
------

I would like to organize a collection of photos of my version of the project.
