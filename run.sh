export __GL_SYNC_TO_VBLANK=1
export __GL_SYNC_DISPLAY_DEVICE=DVI-I-0
export __VDPAU_NVIDIA_SYNC_DISPLAY_DEVICE=DVI-I-0

export SDL_VIDEO_FULLSCREEN_DISPLAY=0 

python kiosk.py & 
python slideshow/display-cocos.py 

killall -KILL python
