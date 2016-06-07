min_resize_time = 0.5

import kivy
kivy.require('1.9.0')

from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, ClearBuffers, ClearColor

import time

class DisplaySource(FloatLayout):
    texture = ObjectProperty(None)

    def __init__(self, client, **kwargs):
        self.client = client
        self.disp_size = [0, 0]
        self.child_size = Window.size

        self.last_resize = 0
        self.resize_trigger = Clock.create_trigger(self.resize)

        self.canvas = RenderContext(use_parent_projection = True)
        with self.canvas:
            self.fbo = Fbo(size = Window.size, use_parent_projection = True)

        with self.fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
        
        super(DisplaySource, self).__init__(**kwargs)
            
        self.texture = self.fbo.texture
        
        Window.bind(on_resize = self.resize)
        
    def resize(self, *args):
        if not time.time() - self.last_resize > min_resize_time:
            self.resize_trigger()
        else:
            print('disp size', self.disp_size)
            if self.disp_size[0] and self.disp_size[1]:
                self.child_size = self.disp_size
#                if not self.fbo.size == self.disp_size: self.fbo.size = self.disp_size
            else:
                self.child_size = Window.size

            self.fbo.size = Window.size
                
            print('resized to', self.fbo.size)

            self.texture = self.fbo.texture
            
            for s in self.client.sections: s.recalc()
            self.last_resize = time.time()
    
    def add_widget(self, *args, **kwargs):
        c = self.canvas
        self.canvas = self.fbo
        super(DisplaySource, self).add_widget(*args, **kwargs)
        self.canvas = c

    def remove_widget(self, *args, **kwargs):
        c = self.canvas
        self.canvas = self.fbo
        super(DisplaySource, self).remove_widget(*args, **kwargs)
        self.canvas = c
        

