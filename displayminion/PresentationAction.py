from kivy.core.window import Window
from kivy.uix.label import Label

import mistune
from .PresentationRenderer import PresentationRenderer

from .Action import Action
from .Fade import Fade

class PresentationAction(Action):
    def __init__(self, *args, **kwargs):
        super(PresentationAction, self).__init__(*args, **kwargs)
        
        self.presentation = self.meteor.find_one('presentations', selector = {'_id': self.action['presentation']})


        self.blank = False
        if not self.args.__contains__('order'):
            self.blank = True
            return

        self.slide = self.meteor.find_one('presentationslides',
            selector = {'presentations': self.presentation['_id'], 'order': self.args['order']})
            
        self.settings = self.combine_settings(self.client.minion.get('settings'),
            self.presentation.get('settings'), self.slide.get('settings'), self.settings)
        
        self.fade_length = float(self.settings.get('presentations_fade', 0.25))
        self.fade_val = 0

        markdown = mistune.Markdown(renderer=PresentationRenderer(settings = self.settings))
        self.text = markdown(self.slide['content'])
        
        self.label = Label(
            text = self.text,
            markup = True,
            text_size = Window.size,
            halign = 'left',
            valign = 'top',
# TODO proper fonts stuff            font_name = self.settings.get('presentations_font'), 
            font_size = float(self.settings.get('presentations_font_size'))
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
