from pyrikura.plugin import Plugin


settings = {}
settings['temp_image'] = 'capture.jpg'


class Translate(Plugin):
    def process(self, msg, sender):
        if msg == chr(1): self.publish([settings['temp_image']])
