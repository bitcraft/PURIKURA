from pyrikura.plugin import Plugin
import pygame



class Tether(Plugin):
    def __init__(self, camera, arduino):
        super(Tether, self).__init__()
        self.arduino = arduino
        self.camera = camera
        self.sound = pygame.mixer.Sound(settings['shutter_sound'])

    def process(self, msg, sender):
        self.sound.play()
        time.sleep(2)
        self.sound.play()
        time.sleep(2)
        self.sound.play()
        time.sleep(2)
        self.sound.play()
        camera.capture(msg)
        self.publish([msg])
        self.arduino.clear()
