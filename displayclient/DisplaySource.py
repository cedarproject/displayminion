import kivy
kivy.require('1.9.0')

from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle, ClearBuffers, ClearColor

class DisplaySource(FloatLayout):
    texture = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.canvas = RenderContext(use_parent_projection=True)

        with self.canvas:
            self.fbo = Fbo(size=Window.size, use_parent_projection=True)
        
        with self.fbo:
            Color(0, 0, 0, 1)
            Rectangle(size=Window.size)

        super(DisplaySource, self).__init__(**kwargs)        
            
        self.canvas.shader.fs = open(resource_find('source.glsl')).read()

        self.texture = self.fbo.texture
        Clock.schedule_interval(self.update_glsl, 0)
        
    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = [float(v) for v in self.size]
        
    def add_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(DisplaySource, self).add_widget(widget)
        self.canvas = c

    def remove_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(DisplaySource, self).remove_widget(widget)
        self.canvas = c
        

