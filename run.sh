export SDL_VIDEO_FULLSCREEN_DISPLAY=0.0

amixer -c 0 set PCM 100%
amixer -c 0 set Master 100%

rm preview.jpg
#python dbus-service.py &
#sleep 1
#python service.py &
#sleep 1
python bin/kiosk.py &&
#python slideshow/display-cocos.py

killall -9 python
