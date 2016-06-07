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
        # Ensures resize is called from the correct thread
        Clock.schedule_once(self._resize, 0)
    
    def _resize(self, *args):
        to_size = list(Window.size)
        if self.disp_size[0] > 0:
            to_size[0] = self.disp_size[0]
        
        if self.disp_size[1] > 0:
            to_size[1] = self.disp_size[1]
            
        print('resizing to', to_size)
        self.child_size = to_size
        self.size = to_size
        self.fbo.size = to_size

        self.texture = self.fbo.texture
        self.texture.min_filter = 'linear'
        self.texture.mag_filter = 'linear'
        
        self.texture.uvsize = (
            to_size[0] / Window.size[0],
            to_size[1] / Window.size[1]
        )
        
        for s in self.client.sections: s.recalc()
        
#        self.texture.save('texture-test.png')
    
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
        

