"""
*
*   copyright: 2012 Leif Theden <leif.theden@gmail.com>
*   license: GPL-3
*
*   This file is part of pyrikura/purikura.
*
*   pyrikura is free software: you can redistribute it and/or modify
*   it under the terms of the GNU General Public License as published by
*   the Free Software Foundation, either version 3 of the License, or
*   (at your option) any later version.
*
*   pyrikura is distributed in the hope that it will be useful,
*   but WITHOUT ANY WARRANTY; without even the implied warranty of
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*   GNU General Public License for more details.
*
*   You should have received a copy of the GNU General Public License
*   along with pyrikura.  If not, see <http://www.gnu.org/licenses/>.
*
"""

"""
display the camera's live preview using pygame.

uses threads and stuff for speed

suitable for any display that is compatable with SDL (framebuffers, etc)
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.join(os.path.abspath(__file__))),
'..'))

import piggyphoto, pygame
import threading, Queue, time
from StringIO import StringIO


class CaptureThread(threading.Thread):
    def __init__(self, queue, camera, lock):
        super(CaptureThread, self).__init__()
        self.queue = queue
        self.camera = camera
        self.lock = lock
    
    def run(self):
        preview = self.camera.capture_preview
        put = self.queue.put
        lock = self.lock
        while 1:
            with lock:
                data = preview().get_data()
            put(data)


class BlitThread(threading.Thread):
    def __init__(self, queue, surface, lock):
        super(BlitThread, self).__init__()
        self.queue = queue
        self.surface = surface
        self.lock = lock

    def run(self):
        get = self.queue.get
        blit = self.surface.blit
        load = pygame.image.load
        lock = self.lock
        while 1:
            picture = load(StringIO(get()))
            with lock:
                blit(picture, (0, 0))


def quit_pressed():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
    return False


clock = pygame.time.Clock()
queue = Queue.Queue(30)

camera_lock = threading.Lock()
camera = piggyphoto.camera()
camera.leave_locked()
camera.capture_preview('preview.jpg')

thread0 = CaptureThread(queue, camera, camera_lock)
thread0.daemon = True
thread0.start()

display_lock = threading.Lock()
picture = pygame.image.load(StringIO(queue.get()))
pygame.display.set_mode(picture.get_size())
main_surface = pygame.display.get_surface()

thread1 = BlitThread(queue, main_surface, display_lock)
thread1.daemon = True
thread1.start()

last_shot = time.time()

print 'running'
flip = pygame.display.flip
while not quit_pressed():
    with display_lock:
        flip()

    if time.time() > last_shot + 10:
        with camera_lock:
            last_shot = time.time()
            camera.capture_image() 

    clock.tick(30)
