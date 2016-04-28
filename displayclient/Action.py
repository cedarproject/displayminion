fade_old_max_wait = 1 # Wait no more than this many seconds to fade out old action

import kivy
kivy.require('1.9.0')

from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.video import Video
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle

class Action:
    def __init__(self, action, old_action, client):
        self.action = action
        self.old_action = old_action

        self.client = client
        self.meteor = self.client.meteor
        self.time = self.client.time
        
        self.settings = action['settings']
        
        self.fade_length = 0
        
        self.ready = False
        self.shown = False
        self.removed = False
        
        self.fades = []
        
        Clock.schedule_once(self.tick, 0)
            
    def combine_settings(self, *args):
        result = {}
        for arg in args:
            if type(arg) == dict: result.update(arg)
            
        return result
            
    def tick(self, dt):
        if not self.removed:
            Clock.schedule_once(self.tick, 0)

            for fade in self.fades[:]:
                fade.tick()
                if fade.finished: self.fades.remove(fade)
                            
    def check_ready(self):
        return True
                
    def show(self):
        self.ready = self.check_ready()

        if self.ready:
            self.shown = True
            
            fade_start = self.time.now()
            fade_end = fade_start + self.fade_length
            
            if self.old_action:
                self.old_action.hide(fade_start, fade_end)
                self.old_action.remove()
                self.old_action = None
                
            self.on_show(fade_start, fade_end)
            
        else:
            if self.old_action and self.time.now() - self.action['time'] / 1000.0 > fade_old_max_wait:
                fade_start = self.time.now()
                fade_end = fade_start + self.fade_length
                
                self.old_action.hide(fade_start, fade_end)
                self.old_action.remove()
                self.old_action = None
                
            Clock.schedule_once(lambda dt: self.show(), 0)
            
    def on_show(self, fade_start, fade_end):
        pass
    
    def hide(self, fade_start = None, fade_end = None):
        if self.shown:
            if not fade_start and not fade_end:
                fade_start = self.time.now()
                fade_end = self.time.now() + self.fade_length
                
            self.on_hide(fade_start, fade_end)
            
    def on_hide(self, fade_start, fade_end):
        self.shown = False
        
    def remove(self):
        if self.shown:
            Clock.schedule_once(lambda dt: self.remove(), 0)
        
        else:
            self.removed = True
