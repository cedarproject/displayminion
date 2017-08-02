import os
import kivy.utils

from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Fbo
from ctypes import Structure, c_void_p, c_int, string_at

from kivy.graphics.opengl import GL_RGBA, GL_UNSIGNED_BYTE, glReadPixels

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp

Gst.init(None)

from .Action import Action

class _MapInfo(Structure):
    _fields_ = [
        ('memory', c_void_p),
        ('flags', c_int),
        ('data', c_void_p)]

class GStreamerOutput:
    def __init__(self, texture):
        self.enabled = True

        if not kivy.utils.platform == 'linux': self.enabled = False
        
        if not self.enabled: return
        
        old_sockets = [f for f in os.listdir('/tmp') if f.startswith('displayminion_shm')]
        for f in old_sockets: os.unlink('/tmp/' + f)
        
        self.pipeline = Gst.Pipeline()
        
        self.appsrc = GstApp.AppSrc(format = Gst.Format.TIME, emit_signals = True, is_live = True)
        self.appsrc.connect('need-data', self.need_data)
                
        self.shmsink = Gst.ElementFactory.make('shmsink')
        self.shmsink.set_property('socket-path', '/tmp/displayminion_shm')
        
        self.pipeline.add(self.appsrc)
        self.pipeline.add(self.shmsink)

        self.appsrc.link(self.shmsink)
        
        self.new_texture(texture)
        
        self.pipeline.set_state(Gst.State.PLAYING)
        
        Clock.schedule_interval(self.update, 0)
    
    def new_texture(self, texture):
        if not self.enabled: return

        self.fbo = Fbo(size = texture.size, texture = texture)
        print('fmt', texture.colorfmt)

        self.update(None)
        self.tex_size = len(self.pixels)

        self.shmsink.set_property('shm-size', self.tex_size * 2)

    def update(self, dt):
        self.pixels = self.fbo.pixels
    
    def stop(self):
        if not self.enabled: return

        self.pipeline.set_state(Gst.State.NULL)

    def need_data(self, *args):
        buf = Gst.Buffer.new_allocate(None, self.tex_size, None)
        buf.fill(0, self.pixels)
        
        self.appsrc.push_buffer(buf)
        
        return False
