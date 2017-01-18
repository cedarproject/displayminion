fade_old_max_wait = 1 # Wait no more than this many seconds to fade out old action

import kivy
kivy.require('1.9.0')

from kivy.animation import Animation
from kivy.clock import Clock

class Action:
    def __init__(self, action, old_action, client):
        self.action = action
        self.old_action = old_action

        self.client = client
        self.meteor = self.client.meteor
        self.time = self.client.time
        
        self.layer = self.action['layer']
        
        self.settings = self.combine_settings(self.client.defaults, self.action.get('settings'))
        self.args = action.get('args', {})
        
        self.fade_length = None
        
        self.ready = False
        self.shown = False
        self.removed = False
        
        self.anim_widgets = []
        self.anims_ended = 0
        
        self.show_schedule_handle = None
    
    def add_anim_widget(self, widget, prop, vin, vout):
        self.anim_widgets.append((widget, prop, vin, vout))
    
    def do_in_animation(self, duration):
        for widget, prop, vin, vout in self.anim_widgets:
            Animation.cancel_all(widget, prop)

            kwargs = {'transition': 'out_quad', 'duration': duration}
            kwargs[prop] = vin
            
            Animation(**kwargs).start(widget)
    
    def do_out_animation(self, duration):
        for widget, prop, vin, vout in self.anim_widgets:
            Animation.cancel_all(widget, prop)

            kwargs = {'transition': 'in_quad', 'duration': duration}
            kwargs[prop] = vout
            
            anim = Animation(**kwargs)
            anim.on_complete = self._out_animation_end
            anim.start(widget)
    
    def _out_animation_end(self, widget):
        self.anims_ended += 1

        if self.anims_ended >= len(self.anim_widgets):
            self.out_animation_end()
        
    def out_animation_end(self):
        pass
            
    def combine_settings(self, *args):
        result = {}
        for arg in args:
            if type(arg) == dict:
                for k, v in arg.items():
                    if not type(v) == type(None):
                        result[k] = v
            
        return result
        
    def get_current_widget_index(self):
        return
                            
    def check_ready(self):
        return True
        
    def get_fade_duration(self):
        if self.fade_length == None:
            if self.old_action and self.old_action.fade_length:
                return self.old_action.fade_length or 0
            else: return 0

        else:
            return self.fade_length
        
    def remove_old(self):
        if self.old_action:        
            self.old_action.hide(self.get_fade_duration())
            self.old_action.remove()
            self.old_action = None
                
    def show(self):
        self.show_schedule_handle = None

        self.ready = self.check_ready()

        if self.ready:
            self.shown = True
            
            self.remove_old()
            self.on_show(self.get_fade_duration())
            
        else:
            if self.old_action and self.time.now() - self.action['time'] > fade_old_max_wait:
                self.remove_old()
                
            self.show_schedule_handle = Clock.schedule_once(lambda dt: self.show(), 0)
            
    def on_show(self, duration):
        pass
    
    def hide(self, duration = None):
        if self.show_schedule_handle: self.show_schedule_handle.cancel()
        
        if self.shown:
            if duration == None: duration = self.get_fade_duration()
            self.on_hide(duration)
            
    def on_hide(self, duration):
        self.shown = False
        
    def remove(self):
        if self.shown:
            Clock.schedule_once(lambda dt: self.remove(), 0)
        
        else:
            self.removed = True
