from zope.interface import Interface, Attribute


class ITrigger(Interface):
    def trigger(self):
        pass


class IImageProcessor(Interface):
    def process(self):
        pass


class IFileOp(Interface):
    def process(self):
        pass


class ICameraProvider(Interface):
    new = Attribute("get a new camera")


class ICamera(Interface):
    capture_preview = Attribute("capture preview")
    capture_image = Attribute("capture image")
    download_preview = Attribute("capture and download preview")
    reset = Attribute("reset the camera")