from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from pyrikura import ipyrikura
import threading
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.shuttercamera")


class CameraFactory(object):
    implements(IPlugin, ipyrikura.ICameraProvider)

    def new(self):
        import shutter

        camera = shutter.Camera()
        return ShutterCamera(camera)


class ShutterCamera(object):
    implements(ipyrikura.ICamera)

    def __init__(self, camera):
        self.capture_filename = 'capture.jpg'
        self.preview_filename = 'preview.jpg'
        self._camera_lock = threading.Lock()
        self._camera = camera

    def capture_preview(self):
        """ Capture a preview image and save to a file

        Returns boolean of succeeded or not
        """
        def capture():
            self._camera.capture_preview(self.preview_filename)

        if self._camera is None:
            logger.debug('want to capture preview, but camera is not setup')
            return False

        d = defer.Deferred()
        d.addCallback(capture)
        return d

    def capture_image(self, filename=None):
        """ Capture a full image and save to a file

        Returns boolean of succeeded or not
        """
        def capture():
            self._camera.capture_image(self.capture_filename)

        if self._camera is None:
            logger.debug('want to capture, but camera is not setup')
            return False

        d = defer.Deferred()
        d.addCallback(capture)
        return d

    def download_preview(self):
        """ Capture preview image and return data
        """
        def capture():
            data = self._camera.capture_preview().get_data()

        d = defer.Deferred()
        d.addCallback(capture)
        return d


factory = CameraFactory()