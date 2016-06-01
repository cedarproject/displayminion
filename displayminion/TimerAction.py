timer_tick_interval = 0.1

from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

import math

from .Action import Action
from .Fade import Fade

# TODO this needs a big rework to be more useful

class TimerAction(Action):
    def __init__(self, *args, **kwargs):
        super(TimerAction, self).__init__(*args, **kwargs)

        self.settings = self.combine_settings(self.settings, self.client.minion.get('settings'), self.action.get('settings'))
        
        self.fade_val = self.settings.get('timers_fade')
        
        t = self.settings.get('timer_time')
        
        # TODO start_at and end_at timers
        if self.settings.get('timers_type') == 'countdown':
            self.target = float(self.action['time']) + float(t['hours']) * 3600 + float(t['minutes']) * 60 + float(t['seconds'])
                        
        self.label = Label(
            markup = True,
            text_size = Window.size,
            halign = self.settings.get('timers_text_align'),
            valign = self.settings.get('timers_text_vertical_align'),
            font_name = self.settings.get('timers_font'),
            font_size = float(self.settings.get('timers_font_size')),
            color = self.settings.get('timers_font_color'),
            outline_width = self.settings.get('timers_font_outline'),
            outline_color = self.settings.get('timers_font_outline_color')
        )
        
        self.label.opacity = 0
        
    def tick(self, dt = None):
        if self.shown:
            t = self.target - self.time.now()
            
            if t < 0:
                sign = '-'
                t = abs(t)
            else:
                sign = ''
            
            hours = math.floor(t / 3600)
            minutes = math.floor((t - hours * 3600) / 60)
            seconds = math.floor(t % 60)
            
            text = '{0}{1:02n}:{2:02n}:{3:02n}'.format(sign, hours, minutes, seconds)
            
            if self.settings.get('timers_font_weight') == 'bold':
                text = '[b]{}[/b]'.format(text)
            
            if sign == '-':
                colorhex = '{0:02x}{1:02x}{2:02x}'.format(*(round(c * 255) for c in self.settings.get('timers_font_negative_color')))
                text = '[color={}]{}[/color]'.format(colorhex, text)              
            elif t < self.settings.get('timers_font_warn_time'):
                colorhex = '{0:02x}{1:02x}{2:02x}'.format(*(round(c * 255) for c in self.settings.get('timers_font_warn_color')))
                text = '[color={}]{}[/color]'.format(colorhex, text)
            
            self.label.text = text
            
            Clock.schedule_once(self.tick, timer_tick_interval)

    def get_current_widget_index(self):
        if self.shown:
            return self.client.source.children.index(self.label)
            
    def fade_tick(self, val):
        self.fade_val = val
        self.label.opacity = val
        
    def fade_out_end(self):
        self.shown = False
        self.client.remove_widget(self.label)
        
    def on_show(self, fade_start, fade_end):
        self.tick()
        self.client.add_layer_widget(self.label, self.layer)
        
        if self.fade: self.fade.stop()
        self.fade = Fade(self.client.time, self.fade_val, 1, fade_start, fade_end, self.fade_tick, None)
            
    def on_hide(self, fade_start, fade_end):
        if self.fade: self.fade.stop()
        self.fade = Fade(self.client.time, self.fade_val, 0, fade_start, fade_end, self.fade_tick, self.fade_out_end)
