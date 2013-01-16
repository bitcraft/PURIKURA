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

suitable for any display that is compatable with SDL (framebuffers, etc)
"""

import piggyphoto, pygame
from StringIO import StringIO
import os
import time

camera = piggyphoto.camera()
camera.leave_locked()
camera.capture_preview('preview.jpg')

picture = pygame.image.load("preview.jpg")
preview_size = picture.get_size()

pygame.display.set_mode(preview_size)
main_surface = pygame.display.get_surface()



def quit_pressed():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
    return False

def update_preview(camera):
    data = camera.capture_preview().get_data()
    picture = pygame.image.load(StringIO(data))
    main_surface.blit(picture, (0, 0))
    pygame.display.flip()


clock = pygame.time.Clock()
while not quit_pressed():
    clock.tick(40)
    update_preview(camera)
