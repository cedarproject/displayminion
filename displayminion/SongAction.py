import kivy.core.text
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle

import re

from .Action import Action
from .Fade import Fade

class SongAction(Action):
    def __init__(self, *args, **kwargs):
        super(SongAction, self).__init__(*args, **kwargs)
        
        self.song = self.meteor.find_one('songs', selector = {'_id': self.action['song']})
        self.arrangement = self.meteor.find_one('songarrangements', selector = {'_id': self.settings['arrangement']})
        
        self.settings = self.combine_settings(self.client.minion.get('settings'), self.song.get('settings'), self.settings)
        
        # TODO if old action is song and it's text is same as current, set fade to 0
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
        print(self.text)
        
        # TODO store fonts on server, download when needed
        # TODO text outlines, once that Kivy feature is complete: https://github.com/kivy/kivy/pull/3816
        
        self.label = Label(
            text = self.text,
            font_name = self.settings.get('songs_font'),
            font_size = float(self.settings.get('songs_font_size'))
        )

        self.label.opacity = 0
        
    def get_current_widget_index(self):
        if self.shown and not self.blank:
            return self.client.source.children.index(self.label)
            
    def fade_tick(self, val):
        self.fade_val = val
        self.label.opacity = val
        
    def fade_out_end(self):
        self.shown = False
        self.client.source.remove_widget(self.label)
        
    def on_show(self, fade_start, fade_end):
        if not self.blank:
            self.client.source.add_widget(self.label, index = self.client.get_widget_index(self))
            
            if self.fade: self.fade.stop()
            self.fade = Fade(self.client.time, self.fade_val, 1, fade_start, fade_end, self.fade_tick, None)
            
    def on_hide(self, fade_start, fade_end):
        if not self.blank:
            if self.fade: self.fade.stop()
            self.fade = Fade(self.client.time, self.fade_val, 0, fade_start, fade_end, self.fade_tick, self.fade_out_end)
