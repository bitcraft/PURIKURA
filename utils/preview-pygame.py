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

suitable for any display that is compatible with SDL (framebuffers, etc)
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
        self._running = False

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        preview = self.camera.capture_preview
        put = self.queue.put
        lock = self.lock
        while self._running:
            with lock:
                data = preview().get_data()
            put(data)


class BlitThread(threading.Thread):
    def __init__(self, queue, surface, lock):
        super(BlitThread, self).__init__()
        self.queue = queue
        self.surface = surface
        self.lock = lock
        self._running = False

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        get = self.queue.get
        blit = self.surface.blit
        load = pygame.image.load
        scale = pygame.transform.scale
        screen = self.surface
        size = self.surface.get_size()
        lock = self.lock
        while self._running:
            image = load(StringIO(get())).convert()
            with lock:
                scale(image, size, screen)


def quit_pressed():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        elif event.type == pygame.KEYDOWN:
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return True
    return False


if __name__ == '__main__':
    pygame.display.set_mode((0,0), pygame.FULLSCREEN |
                                   pygame.DOUBLEBUF |
                                   pygame.HWSURFACE)

    main_surface = pygame.display.get_surface()

    pygame.mouse.set_visible(False)

    display_lock = threading.Lock()
    camera_lock = threading.Lock()
    queue = Queue.Queue(10)
    camera = piggyphoto.camera()

    thread0 = CaptureThread(queue, camera, camera_lock)
    thread0.daemon = True
    thread0.start()

    thread1 = BlitThread(queue, main_surface, display_lock)
    thread1.daemon = True
    thread1.start()

    clock = pygame.time.Clock()
    flip = pygame.display.flip
    try:
        while not quit_pressed():
            with display_lock:
                flip()
            clock.tick(30)
    finally:
        thread0.stop()
        thread1.stop()
        time.sleep(1)
        camera.exit()
