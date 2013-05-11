from pyrikura.plugin import Plugin
import piggyphoto



class PBCamera(Plugin):

    def capture(self, filename=None):
        self.camera.capture_image(filename)

    def init_camera(self):
        c = piggyphoto.camera()
        c.leave_locked()
        self.camera = c
