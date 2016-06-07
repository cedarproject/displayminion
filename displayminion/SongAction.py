from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

import re

from .Action import Action
from .Fade import Fade

class SongAction(Action):
    def __init__(self, *args, **kwargs):
        super(SongAction, self).__init__(*args, **kwargs)
        
        self.song = self.meteor.find_one('songs', selector = {'_id': self.action['song']})
        self.arrangement = self.meteor.find_one('songarrangements', selector = {'_id': self.settings['arrangement']})
        
        self.settings = self.combine_settings(self.settings, self.client.minion.get('settings'), self.song.get('settings'), self.action.get('settings'))
        
        self.fade_length = float(self.settings.get('songs_fade'))
        self.fade_val = 0
        
        self.blank = False
        if not self.args.__contains__('section'):
            self.blank = True
            return
        
        self.section = self.meteor.find_one('songsections', selector = {'_id': self.arrangement['order'][self.args['section']]})
        self.contents = self.section['contents'][self.args['index']]['text']
        
        # Removes text between square brackets and replaces multiple consecutive spaces with a single space
        self.text = re.sub(r' +', ' ', re.sub(r'\[(.*?)\]', '', self.contents)).strip()

        if self.settings.get('songs_font_weight') == 'bold':
            self.text = '[b]{}[/b]'.format(self.text)

        self.size_hint = [
            float(self.settings.get('songs_width')) * 0.01,
            float(self.settings.get('songs_height')) * 0.01
        ]
        
        self.size = [
            Window.size[0] * self.size_hint[0],
            Window.size[1] * self.size_hint[1]
        ]
        
        self.pos = [0, 0]
        self.bg_pos = [0, 0]
        
        if self.settings.get('songs_position_horizontal') == 'left':
            self.pos[0] = Window.size[0] * -(1 - self.size_hint[0]) / 2.0
            self.bg_pos[0] = 0
        elif self.settings.get('songs_position_horizontal') == 'center':
            self.pos[0] = 0
            self.bg_pos[0] = (Window.size[0] / 2.0) - (self.size[0] / 2.0)
        elif self.settings.get('songs_position_horizontal') == 'right':
            self.pos[0] = Window.size[0] * (1 - self.size_hint[0]) / 2.0
            self.bg_pos[0] = Window.size[0] - self.size[0]
            
        if self.settings.get('songs_position_vertical') == 'top':
            self.pos[1] = Window.size[1] * (1 - self.size_hint[1]) / 2.0
            self.bg_pos[1] = Window.size[1] - self.size[1]
        elif self.settings.get('songs_position_vertical') == 'center':
            self.pos[1] = 0
            self.bg_pos[1] = (Window.size[1] / 2.0) - (self.size[1] / 2.0)
        elif self.settings.get('songs_position_vertical') == 'bottom':
            self.pos[1] = Window.size[1] * -(1 - self.size_hint[1]) / 2.0
            self.bg_pos[1] = 0
            
        self.label = Label(
            text = self.text,
            markup = True,
            text_size = self.size,
            size = self.size,
            pos = self.pos,
            halign = self.settings.get('songs_align_horizontal'),
            valign = self.settings.get('songs_align_vertical'),
            font_name = self.settings.get('songs_font'), 
            font_size = float(self.settings.get('songs_font_size')),
            color = self.settings.get('songs_font_color'),
            outline_width = self.settings.get('songs_font_outline'),
            outline_color = self.settings.get('songs_font_outline_color')
        )
        
        with self.label.canvas.before:
            Color(*self.settings.get('songs_background_color'))
            Rectangle(size = self.size, pos = self.bg_pos)

        self.label.opacity = 0
        
    def get_current_widget_index(self):
        if self.shown and not self.blank:
            return self.client.source.children.index(self.label)
            
    def fade_tick(self, val):
        self.fade_val = val
        self.label.opacity = val
        
    def fade_out_end(self):
        self.shown = False
        self.client.remove_widget(self.label)
        
    def on_show(self, fade_start, fade_end):
        if not self.blank:
            self.client.add_layer_widget(self.label, self.layer)
            
            if self.fade: self.fade.stop()
            self.fade = Fade(self.client.time, self.fade_val, 1, fade_start, fade_end, self.fade_tick, None)
            
    def on_hide(self, fade_start, fade_end):
        if not self.blank:
            if self.fade: self.fade.stop()
            self.fade = Fade(self.client.time, self.fade_val, 0, fade_start, fade_end, self.fade_tick, self.fade_out_end)
