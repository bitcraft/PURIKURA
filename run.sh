export SDL_VIDEO_FULLSCREEN_DISPLAY=0.0

amixer -c 0 set PCM 100% 
python dbus-service.py &
python kiosk.py &
#sleep 5 &&

#python slideshow/display-cocos.py 

killall -KILL python
