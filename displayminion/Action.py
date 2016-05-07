fade_old_max_wait = 1 # Wait no more than this many seconds to fade out old action

import kivy
kivy.require('1.9.0')

from kivy.clock import Clock

class Action:
    def __init__(self, action, old_action, client):
        self.action = action
        self.old_action = old_action

        self.client = client
        self.meteor = self.client.meteor
        self.time = self.client.time
        
        self.layer = self.action['layer']
        
        self.settings = action.get('settings', {})
        self.args = action.get('args', {})
        
        self.fade_length = False
        
        self.ready = False
        self.shown = False
        self.removed = False
        
        self.fade = None        
            
    def combine_settings(self, *args):
        result = {}
        for arg in args:
            if type(arg) == dict: result.update(arg)
            
        return result
                            
    def check_ready(self):
        return True
        
    def get_fade_start_end(self):
        if self.fade_length == None:
            return self.time.now(), self.time.now() + (self.old_action.fade_length or 0)
        else:
            return self.time.now(), self.time.now() + self.fade_length
        
    def remove_old(self, fade_start, fade_end):
        if self.old_action:        
            self.old_action.hide(fade_start, fade_end)
            self.old_action.remove()
            self.old_action = None        
                
    def show(self):
        self.ready = self.check_ready()

        if self.ready:
            self.shown = True
            
            fade_start, fade_end = self.get_fade_start_end()
            
            self.remove_old(fade_start, fade_end)
            self.on_show(fade_start, fade_end)
            
        else:
            if self.old_action and self.time.now() - self.action['time'] / 1000.0 > fade_old_max_wait:
                fade_start, fade_end = self.get_fade_start_end()
                
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
