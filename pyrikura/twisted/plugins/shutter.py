from zope.interface import implements
from twisted.plugin import IPlugin
from pyrikura import ipyrikura
import threading
import logging
import shutter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.shuttercamera")


class CameraProvider(object):
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
        if self._camera is None:
            logger.debug('want to capture preview, but camera is not setup')
            return False

        with self._camera_lock:
            try:
                self._camera.capture_preview(self.preview_filename)
                return True
            except shutter.ShutterError as e:
                if e.result == -1:
                    logger.debug('unable to focus camera')
                else:
                    logger.debug('unhandled error {}', e.result)
                return False

    def capture_image(self, filename=None):
        """ Capture a full image and save to a file

        Returns boolean of succeeded or not
        """
        if self._camera is None:
            logger.debug('want to capture, but camera is not setup')
            return False

        if filename is None:
            filename = self.capture_filename

        with self._camera_lock:
            try:
                self._camera.capture_image(self.capture_filename)
                return True
            except shutter.ShutterError as e:
                if e.result == -1:
                    logger.debug('unable to focus camera')
                else:
                    logger.debug('unhandled error {}', e.result)
                return False

    def download_preview(self):
        """ Capture preview image and return data
        """
        if self._camera is None:
            logger.debug('want to get preview, but camera is not setup')
            return False

        with self._camera_lock:
            try:
                data = self._camera.capture_preview().get_data()
            except shutter.ShutterError as e:
                logger.error("failed to download capture data")


provider = CameraProvider()