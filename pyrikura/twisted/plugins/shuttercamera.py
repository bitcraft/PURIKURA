from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.internet import defer
from twisted.internet import interfaces
from twisted.internet import threads
from twisted.protocols import basic
from pyrikura.config import Config
from pyrikura import ipyrikura
import threading
import logging
import time

from struct import pack, unpack, calcsize

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("purikura.shuttercamera")


class PreviewProducer(object):
    implements(interfaces.IPushProducer)

    def __init__(self, proto, camera):
        self._proto = proto
        self._camera = camera
        self._paused = False

    def pauseProducing(self):
        self._paused = True

    @defer.inlineCallbacks
    def resumeProducing(self):
        self._paused = False
        data = yield self._camera.download_preview()
        self._proto.sendString(data)
        self._proto.transport.unregisterProducer()
        self._proto.transport.loseConnection()

    def stopProducing(self):
        pass


class ServePreviews(basic.Int32StringReceiver):
    fmt = '!I'

    def __init__(self, camera):
        self._camera = camera

    def connectionMade(self):
        p = PreviewProducer(self, self._camera)
        self.transport.registerProducer(p, True)
        p.resumeProducing()

    def connectionLost(self, reason):
        pass

    def sendString(self, data):
        self.transport.write(pack(self.fmt, len(data)) + data)


class ShutterCamera(object):
    implements(ipyrikura.ICamera)

    def __init__(self, *args, **kwargs):
        import shutter
        self.capture_filename = 'capture.jpg'
        self.preview_filename = 'preview.jpg'
        self._camera = shutter.Camera(*args, **kwargs)
        self._lock = threading.Lock()

    def create_producer(self):
        return ServePreviews(self)

    def reset(self):
        import shutter
        with self._lock:
            self._camera = None
            self._camera = shutter.Camera()

    def capture_preview(self):
        """ Capture a preview image and save to a file
        """
        def capture():
            with self._lock:
                self._camera.capture_preview(self.preview_filename)
            return self.preview_filename

        return threads.deferToThread(capture)

    def capture_image(self, filename=None):
        """ Capture a full image and save to a file
        """
        def capture():
            with self._lock:
                #self._camera.capture_image(self.capture_filename)
                pass
            return self.capture_filename

        return threads.deferToThread(capture)

    def download_preview(self):
        """ Capture preview image and return data
        """
        def capture():
            with self._lock:
                return self._camera.capture_preview().get_data()

        return threads.deferToThread(capture)


class ShutterCameraFactory(object):
    implements(IPlugin, ipyrikura.IPyrikuraPlugin)
    __plugin__ = ShutterCamera

    @classmethod
    def new(cls, *args, **kwargs):
        return cls.__plugin__(*args, **kwargs)

factory = ShutterCameraFactory()
