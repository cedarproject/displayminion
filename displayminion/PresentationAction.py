from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle

#from kivy.loader import Loader
#Loader.loading_image = ''

import sys
import math
import urllib.parse

from .PresentationRenderer import presentation_renderer

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
            selector = {'presentation': self.presentation['_id'], 'order': self.args['order']})
            
        self.settings = self.combine_settings(self.settings, self.client.minion.get('settings'),
            self.presentation.get('settings'), self.slide.get('settings'), self.action.get('settings'))
        
        self.fade_length = float(self.settings.get('presentations_fade', 0.25))
        self.fade_val = 0
        
#        try:
        self.text = presentation_renderer(self.slide['content'], self.settings, self.args)
#        except:
#            print(sys.exc_info()[0])
#            self.text = 'Error loading slide:\n' + str(sys.exc_info()[0])
        
        mediaurl = self.meteor.find_one('settings', selector={'key': 'mediaurl'})['value']

        self.imageids = self.slide.get('images', [])
        self.images = []
        
        for _id in self.imageids:
            m = self.meteor.find_one('media', selector = {'_id': _id})
            url = 'http://{}{}'.format(self.client.server, urllib.parse.quote(mediaurl + m['location']))

            i = AsyncImage(source = url)
            i.allow_stretch = True
            self.images.append(i)
        
        self.size_hint = [
            float(self.settings.get('presentations_width')) * 0.01,
            float(self.settings.get('presentations_height')) * 0.01
        ]
        
        self.bg_size = [
            Window.size[0] * self.size_hint[0],
            Window.size[1] * self.size_hint[1]
        ]
        
        self.pos = {'x': 0, 'y': 0}
        self.bg_pos = [0, 0]
        
        if self.settings.get('presentations_position_horizontal') == 'left':
            self.pos['x'] = -1
            self.bg_pos[0] = 0
        elif self.settings.get('presentations_position_horizontal') == 'center':
            self.pos['x'] = -0.5 - (self.size_hint[0] / 2.0)
            self.bg_pos[0] = (Window.size[0] / 2.0) - (self.bg_size[0] / 2.0)
        elif self.settings.get('presentations_position_horizontal') == 'right':
            self.pos['x'] = -self.size_hint[0]
            self.bg_pos[0] = Window.size[0] - self.bg_size[0]
            
        if self.settings.get('presentations_position_vertical') == 'top':
            self.pos['y'] = -self.size_hint[1]
            self.bg_pos[1] = Window.size[1] - self.bg_size[1]
        elif self.settings.get('presentations_position_vertical') == 'center':
            self.pos['y'] = -0.5 - (self.size_hint[1] / 2.0)
            self.bg_pos[1] = (Window.size[1] / 2.0) - (self.bg_size[1] / 2.0)
        elif self.settings.get('presentations_position_vertical') == 'bottom':
            self.pos['y'] = -1
            self.bg_pos[1] = 0
            
        if len(self.text.strip()) and len(self.images):
            self.do_text = True
            self.do_images = True

            side = self.settings.get('presentations_image_side')
            
            if side == 'left':
                self.pres_pos = {'x': self.pos['x'] + self.size_hint[0] / 2.0, 'y': self.pos['y']}
                self.pres_size = [self.size_hint[0] / 2.0, self.size_hint[1]]
                self.img_pos = {'x': self.pos['x'], 'y': self.pos['y']}
                self.img_size = [self.size_hint[0] / 2.0, self.size_hint[1]]
            if side == 'right':
                self.pres_pos = {'x': self.pos['x'], 'y': self.pos['y']}
                self.pres_size = [self.size_hint[0] / 2.0, self.size_hint[1]]
                self.img_pos = {'x': self.pos['x'] + self.size_hint[0] / 2.0, 'y': self.pos['y']}
                self.img_size = [self.size_hint[0] / 2.0, self.size_hint[1]]
            if side == 'top':
                self.pres_pos = {'x': self.pos['x'], 'y': self.pos['y']}
                self.pres_size = [self.size_hint[0], self.size_hint[1] / 2.0]
                self.img_pos = {'x': self.pos['x'], 'y': self.pos['y'] + self.size_hint[1] / 2.0}
                self.img_size = [self.size_hint[0], self.size_hint[1] / 2.0]
            if side == 'bottom':
                self.pres_pos = {'x': self.pos['x'], 'y': self.pos['y'] + self.size_hint[1] / 2.0}
                self.pres_size = [self.size_hint[0], self.size_hint[1] / 2.0]
                self.img_pos = {'x': self.pos['x'], 'y': self.pos['y']}
                self.img_size = [self.size_hint[0], self.size_hint[1] / 2.0]
                
        elif len(self.text.strip()):
            self.do_text = True
            self.do_images = False
            
            self.pres_pos = self.pos
            self.pres_size = self.size_hint
        
        else:
            self.do_images = True
            self.do_text = False
            
            self.img_pos = self.pos
            self.img_size = self.size_hint
            
        self.bg = Widget()

        with self.bg.canvas.before:
            Color(*self.settings.get('presentations_background_color'))
            Rectangle(size = self.bg_size, pos = self.bg_pos)
            
        self.bg.opacity = 0

        self.label = None
        self.layout = None            

        if self.do_text:
            self.pres_text_size = [Window.size[0] * self.pres_size[0], Window.size[1] * self.pres_size[1]]

            self.label = Label(
                text = self.text,
                markup = True,
                text_size = self.pres_text_size,
                size_hint = self.pres_size,
                pos_hint = self.pres_pos,
                halign = self.settings.get('presentations_align_horizontal'),
                valign = self.settings.get('presentations_align_vertical'),
                font_name = self.settings.get('presentations_font'),
                font_size = round(float(self.settings.get('presentations_font_size'))),
                color = self.settings.get('presentations_font_color'),
                outline_width = self.settings.get('presentations_font_outline'),
                outline_color = self.settings.get('presentations_font_outline_color')
            )
            
            self.label.opacity = 0
            
        if self.do_images:
            rows = round(math.sqrt(len(self.images)))
            
            self.layout = GridLayout(rows = rows, size_hint = self.img_size, pos_hint = self.img_pos)
            for image in self.images: self.layout.add_widget(image)
            
            self.layout.opacity = 0
        
    def get_current_widget_index(self):
        if self.shown and not self.blank:
            i = [self.client.source.children.index(self.bg)]
            if self.label: i.append(self.client.source.children.index(self.label))
            if self.layout: i.append(self.client.source.children.index(self.layout))
            return max(i)
            
    def fade_tick(self, val):
        self.fade_val = val
        
        self.bg.opacity = val
        if self.label: self.label.opacity = val
        if self.layout: self.layout.opacity = val
        
    def fade_out_end(self):
        self.shown = False
        
        self.client.remove_widget(self.bg)
        if self.label: self.client.remove_widget(self.label)
        if self.layout: self.client.remove_widget(self.layout)

    def check_ready(self):
        for image in self.images:
            if not image._coreimage.loaded:
                return False

        return True
        
    def on_show(self, fade_start, fade_end):
        if not self.blank:
            self.client.add_layer_widget(self.bg, self.layer)
            if self.label: self.client.add_layer_widget(self.label, self.layer)
            if self.layout: self.client.add_layer_widget(self.layout, self.layer)
            
            if self.fade: self.fade.stop()
            self.fade = Fade(self.client.time, self.fade_val, 1, fade_start, fade_end, self.fade_tick, None)
            
    def on_hide(self, fade_start, fade_end):
        if not self.blank:
            if self.fade: self.fade.stop()
            self.fade = Fade(self.client.time, self.fade_val, 0, fade_start, fade_end, self.fade_tick, self.fade_out_end)
