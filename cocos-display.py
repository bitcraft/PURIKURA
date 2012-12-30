import cocos
from cocos.actions import *
import pyglet


class Tablecloth(cocos.layer.Layer):
    def __init__(self):
        super(Tablecloth, self).__init__()


class PhotoLayer(cocos.layer.Layer):
    def __init__(self):
        super(PhotoLayer, self).__init__()
        self.schedule_interval(self.new_photo, 5)
        self.batch = cocos.batch.BatchNode()
        self.add(self.batch)
        self.new_photo()
        
    def new_photo(self, dt=0):
        time = 20
        top = 200
        width, height = cocos.director.director.get_window_size()
        filename = 'photo.jpg'
        sprite = cocos.sprite.Sprite(filename)
        #sprite.schedule_once(sprite.kill, time)
        sprite.scale = 0.25
        sprite_w = sprite.width * sprite.scale
        sprite.position = width + sprite_w*3, top
        self.batch.add(sprite)
        sprite.do(MoveTo((-sprite_w*2, top), 20))


cocos.director.director.init(fullscreen=True)

background = Tablecloth()

main_scene = cocos.scene.Scene(background, PhotoLayer())
cocos.director.director.run(main_scene)
