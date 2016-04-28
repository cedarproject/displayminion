import kivy
kivy.require('1.9.0')

from kivy.uix.image import Image
from kivy.uix.video import Video
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle

from .Action import Action
from .Fade import Fade

# Widget layers can work by using the index param of add_widget TODO

class MediaAction(Action):
    def __init__(self, action, old_action, client):
        super(MediaAction, self).__init__(action, old_action, client)

        self.media = self.meteor.find_one('media', selector={'_id': action.get('media')})
        
        self.settings = self.combine_settings(self.client.minion.get('settings'), self.media.get('settings'), self.settings)
        
        self.fade_length = float(self.settings.get('media_fade', 1))
        
        if self.media['type'] == 'video':
            mediaurl = self.meteor.find_one('settings', selector={'key': 'mediaurl'})['value']
            self.sourceurl = 'http://{}{}'.format(self.client.server, mediaurl + self.media['location'])

        self.video = Video(source = self.sourceurl)
        self.video.allow_stretch = True
#        self.video.keep_ratio = True

        self.video.opacity = 0
        self.video.volume = 0
        self.video.play = True # Convince video to preload itself TODO find better way
                
    def fade_tick(self, val):
        self.video.opacity = val
        self.video.volume = val
        
    def fade_out_end(self):
        self.shown = False
        self.video.play = False
        self.client.source.remove_widget(self.video)
        
    def check_ready(self):
        if self.video.loaded:
#            self.video.seek(0) # TODO can't seek until HTTP Range stuff implemented
            return True
        
    def on_show(self, fade_start, fade_end):
        self.video.play = True
        self.client.source.add_widget(self.video)
        
        self.fades.append(Fade(self.client.time, 0, 1, fade_start, fade_end, self.fade_tick, None))
        
    def on_hide(self, fade_start, fade_end):
        self.fades.append(Fade(self.client.time, 1, 0, fade_start, fade_end, self.fade_tick, self.fade_out_end))
