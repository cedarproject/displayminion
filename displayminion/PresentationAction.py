from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image, AsyncImage
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle

import sys
import math
import urllib.parse
import io
import gi
import cairo

gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')

from gi.repository import Pango, PangoCairo

from .PresentationRenderer import presentation_renderer

from .Action import Action

class PresentationAction(Action):
    def __init__(self, *args, **kwargs):
        super(PresentationAction, self).__init__(*args, **kwargs)
        
        if self.action['type'] == 'presentation':
            self.presentation = self.meteor.find_one('presentations', selector = {'_id': self.action['presentation']})

            self.blank = False
            if not self.args.__contains__('order'):
                self.blank = True
                return

            self.slide = self.meteor.find_one('presentationslides',
                selector = {'presentation': self.presentation['_id'], 'order': self.args['order']})
        
        elif self.action['type'] == 'presentationslide':
            self.slide = self.meteor.find_one('presentationslides', selector = {'_id': self.action['presentationslide']})
            self.presentation = self.meteor.find_one('presentations', selector = {'_id': self.slide['presentation']})
            self.blank = False
            
        self.settings = self.combine_settings(self.settings, self.client.minion.get('settings'),
            self.presentation.get('settings'), self.slide.get('settings'), self.action.get('settings'))
        
        mediaurl = self.meteor.find_one('settings', selector={'key': 'mediaurl'})['value']

        self.image_side = self.settings.get('presentations_image_side')
        
        self.fade_length = float(self.settings.get('presentations_fade', 0.25))
        self.fade_val = 0
                
        if self.presentation.get('imported'):
            self.text = ''

            url = 'http://{}{}'.format(self.client.server, urllib.parse.quote(mediaurl + '/' + self.slide['imagepath']))
            i = AsyncImage(source = url)
            i.allow_stretch = True
            self.images = [i]
        
        else:
            self.text = self.slide['content']
            self.has_text = True # TODO add text-finding logic!

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
        
        self.size = [
            self.client.source.child_size[0] * self.size_hint[0],
            self.client.source.child_size[1] * self.size_hint[1]
        ]
        
        self.pos = [0, 0]
       
        if self.settings.get('presentations_position_horizontal') == 'left':
            self.pos[0] = 0
        elif self.settings.get('presentations_position_horizontal') == 'center':
            self.pos[0] = (self.client.source.child_size[0] / 2.0) - (self.size[0] / 2.0)
        elif self.settings.get('presentations_position_horizontal') == 'right':
            self.pos[0] = self.client.source.child_size[0] - self.size[0]
            
        if self.settings.get('presentations_position_vertical') == 'top':
            self.pos[1] = self.client.source.child_size[1] - self.size[1]
        elif self.settings.get('presentations_position_vertical') == 'center':
            self.pos[1] = (self.client.source.child_size[1] / 2.0) - (self.size[1] / 2.0)
        elif self.settings.get('presentations_position_vertical') == 'bottom':
            self.pos[1] = 0
            
        self.layout = BoxLayout(
            orientation = ('vertical' if self.image_side in ('top', 'bottom') else 'horizontal'),
            pos = self.pos,
            size = self.size,
            size_hint = [None, None]
        )

        self.layout.opacity = 0
            
        self.bg = Widget()

        with self.bg.canvas.before:
            Color(*self.settings.get('presentations_background_color'))
            Rectangle(size = self.size, pos = self.pos)
            
        self.bg.canvas.opacity = 0

        self.label = None
        self.image_layout = None

        if self.has_text:
            self.text_size = list(self.size)
            if self.images and self.image_side in ('left', 'right'):
                self.text_size[0] /= 2.0
            elif self.images:
                self.text_size[1] /= 2.0
            
            self.text_size[0] -= int(self.settings.get('presentations_text_margin_horizontal')) * 2
            self.text_size[1] -= int(self.settings.get('presentations_text_margin_vertical')) * 2

            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 320, 120)
            context = cairo.Context(surf)
            context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
            pangocairo_context = PangoCairo.create_context(context)

            layout = Pango.Layout.new(pangocairo_context)
            fontname = "Code Pro LC"
            font = Pango.FontDescription(fontname + " 25")
            layout.set_font_description(font)

            layout.set_text(u"Hello World\nHello World 2\nHello World 3\n\n\nBlah", -1)
            context.set_source_rgb(255, 255, 255)
            PangoCairo.update_layout(context, layout)
            PangoCairo.show_layout(context, layout)

#            layout2 = Pango.Layout.new(pangocairo_context)
#            layout2.set_font_description(font)
            
#            layout2.set_text(u"Hello World 2", -1)
#            context.set_source_rgb(255, 255, 255)
#            PangoCairo.update_layout(context, layout2)
#            PangoCairo.show_layout(context, layout2)

            imagefile = io.BytesIO()
            surf.write_to_png(imagefile)         
            imagefile.seek(0)
            imagedata = CoreImage(imagefile, ext = 'png')
            
            self.label = Image(texture = imagedata.texture)
            
        if self.images:
            rows = round(math.sqrt(len(self.images)))
            
            self.image_layout = GridLayout(rows = rows)
            for image in self.images: self.image_layout.add_widget(image)
            
    def get_current_widget_index(self):
        if self.shown and not self.blank:            
            return max(self.client.source.children.index(self.bg), self.client.source.children.index(self.layout))
        
    def out_animation_end(self):
        self.shown = False
        
        self.client.remove_widget(self.bg)
        self.client.remove_widget(self.layout)
        if self.label: self.client.remove_widget(self.label)
        if self.image_layout: self.client.remove_widget(self.image_layout)

    def check_ready(self):
        if self.blank: return True

        for image in self.images:
            if not image._coreimage.loaded:
                return False

        return True
        
    def on_show(self, fade_length):
        if not self.blank:
            self.client.add_layer_widget(self.bg, self.layer)
            self.add_anim_widget(self.bg.canvas, 'opacity', 1, 0)

            self.client.add_layer_widget(self.layout, self.layer)
            self.add_anim_widget(self.layout, 'opacity', 1, 0)
            
            if self.image_side in ('top', 'left'):
                if self.image_layout: self.layout.add_widget(self.image_layout)
                if self.label: self.layout.add_widget(self.label)
            else:
                if self.label: self.layout.add_widget(self.label)
                if self.image_layout: self.layout.add_widget(self.image_layout)
            
            self.do_in_animation(fade_length)
            
    def on_hide(self, fade_length):
        if not self.blank:
            self.do_out_animation(fade_length)
