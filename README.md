PURIKURA
========

PURIKURA is a set of hardware and software plans for a DIY wedding photo booth.

It is capable of producing excellent looking 2x6 inch color photo strips with 4 photos.


Suggested Use
-------------

The booth is activated by pulling a rope inside the booth and activating a switch connected to the arduino.  The photos are sent to the computer and a print is quickly produced and ready in just under one minute.


Details
-------

The arduino is connected to a button and the camera.  The button is a simple microswitch.  When connected to the camera, it behaves exactly like a electronic shutter release cable.  When the picture taking cycle is started, the arduino triggers 4 photos 3 seconds apart.

Inside the camera is a Eye-Fi X2 SD card with wifi.  As soon as the picture is taken, the photo is sent to the computer.  Once there are four new photos on the computer, a python script uses GraphicsMagick to compose a print and the resulting image is sent to the printer.

Finally, the photos are added to iPhoto and moved to another location for storage.


The Name
--------
 
'purukura' is a term used in Japan for their ubiquitous style of photo booths.


Hardware
--------

-  Eye-Fi X2 card (any model)
-  Panasonic Lumix GF-1
-  MacBook Pro, late 2011
-  Arduino Uno
-  Epson PictureMate Charm (PM 225)
-  Apple TV, 2nd Generation



Software
--------

-  Arduino
-  Apple OS X
-  Python 2.7
-  GraphicsMagick
-  Apple Automator
-  iPhoto '11


Future
------

I would like to organize a collection of photos of my version of the project.