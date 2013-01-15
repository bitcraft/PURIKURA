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
