export SDL_VIDEO_FULLSCREEN_DISPLAY=0.0

python kiosk.py & 
sleep 5 &&

python slideshow/display-cocos.py 

killall -KILL python
