import kivy
kivy.require('1.9.0')

from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, ClearBuffers, ClearColor

class DisplaySource(FloatLayout):
    texture = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.sections = []

        self.canvas = RenderContext(use_parent_projection = True)
        with self.canvas:
            self.fbo = Fbo(size = Window.size, use_parent_projection = True)

        with self.fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
        
        super(DisplaySource, self).__init__(**kwargs)
            
        self.texture = self.fbo.texture
        
        Window.bind(on_resize = self.resize)
        
    def resize(self, window, width, height):
        self.fbo.size = Window.size
        self.texture = self.fbo.texture
                    
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
        

