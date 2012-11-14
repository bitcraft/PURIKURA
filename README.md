PURIKURA
========

PURIKURA is a set of hardware and software plans for a DIY wedding photo booth.

It is capable of producing excellent looking 2x6 inch color photo strips with 4 square photos.


Suggested Use
-------------

The booth is activated by pulling a rope inside the booth that activates a switch connected to the arduino.  The photos are sent to the computer with a 4gb eye-fi card in direct mode and a print is quickly produced with python and graphicsmagick and in just under one minute.


Details
-------

The arduino is connected to a button and the camera.  The button is a simple microswitch connected to a rope.  
The arduino has a simple shield that mimicks a shutter release cable using two relays.

Inside the camera is a Eye-Fi X2 4gb SD card with wifi.  As soon as the picture is taken, the photo is sent to the computer.  The python script continously monitors the incoming photo folder and once there are four new photos on the computer, the script uses GraphicsMagick to compose a print and the resulting image is sent to the printer.


The Name
--------
 
'purukura' is a term used in Japan for their ubiquitous style of photo booths.


Hardware
--------

-  Eye-Fi X2 card (any capacity)
-  Panasonic Lumix GF-1
-  MacBook Pro, late 2011
-  Arduino Uno
-  Epson PictureMate Charm (PM 225)



Software
--------

-  Arduino
-  Apple OS X
-  Python 2.7
-  Pygame (for sound)
-  GraphicsMagick


Future
------

I would like to organize a collection of photos of my version of the project.
