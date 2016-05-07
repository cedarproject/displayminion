media_sync_interval = 0.25
media_sync_tolerance = 0.1

import kivy
kivy.require('1.9.0')

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.image import AsyncImage
from kivy.uix.video import Video
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle

from .Action import Action
from .Fade import Fade

class MediaAction(Action):
    def __init__(self, action, old_action, client):
        super(MediaAction, self).__init__(action, old_action, client)

        self.media = self.meteor.find_one('media', selector={'_id': action.get('media')})
        self.duration = float(self.media['duration'])
        
        self.settings = self.combine_settings(self.client.minion.get('settings'), self.media.get('settings'), self.settings)
        
        self.fade_length = float(self.settings.get('media_fade', 1))
        self.fade_val = 0
        
        mediaurl = self.meteor.find_one('settings', selector={'key': 'mediaurl'})['value']
        self.sourceurl = 'http://{}{}'.format(self.client.server, mediaurl + self.media['location'])
        
        self.video = None
        self.audio = None
        self.image = None
        
        self.to_sync = None

        if self.media['type'] == 'video':
            self.video = Video(source = self.sourceurl)
            self.to_sync = self.video
            self.video.allow_stretch = True
            
            if self.settings.get('media_preserve_aspect') == 'no':
                self.video.keep_ratio = False

            self.video.opacity = 0
            self.video.volume = 0            
            self.video.state = 'play' # Convince video to preload itself - TODO find better way
            
        elif self.media['type'] == 'audio':
            self.audio = SoundLoader.load(self.sourceurl)
            self.to_sync = self.audio
            self.audio.volume = 0
        
        elif self.media['type'] == 'image':
            self.image = AsyncImage(source = self.sourceurl)
            self.image.allow_stretch = True

            if self.settings.get('media_preserve_aspect') == 'no':
                self.image.keep_ratio = False
            
            self.image.opacity = 0
            
    def get_current_widget_index(self):
        if self.shown:
            if self.video:
                return self.client.source.children.index(self.video)

            elif self.image:
                return self.client.source.children.index(self.image)
            
        return None
        
    def get_media_time(self):
        diff = self.client.time.now() - float(self.action['time'])

        if diff > 0 and self.settings.get('media_loop') == 'yes':
            diff = diff % self.duration
        
        if diff > self.duration: diff = self.duration
        
        print(diff, self.duration)
        return diff
        
    def media_sync(self, dt = None):
        if self.shown:
            if self.video: pos = self.video.position
            elif self.audio: pos = self.audio.get_pos()
                
            if self.to_sync and abs(self.get_media_time() - pos) > media_sync_tolerance:
                if self.settings.get('media_loop') == 'no' and pos > self.duration:
                    if self.video: self.to_sync.state = 'stop'
                    elif self.audio: self.audio.stop()
                else:
                    self.to_sync.seek(self.get_media_time())
                
            Clock.schedule_once(self.media_sync, media_sync_interval)
            
    def fade_tick(self, val):
        self.fade_val = val

        if self.video:
            self.video.opacity = val
            self.video.volume = val

        elif self.audio:
            self.audio.volume = val
            
        elif self.image:
            self.image.opacity = val
        
    def fade_out_end(self):
        self.shown = False
        
        if self.video:
            self.video.state = 'pause'
            self.client.source.remove_widget(self.video)
            
        elif self.audio:
            self.audio.stop()
        
    def check_ready(self):
        if self.get_media_time() >= 0:
            if self.video and self.video.loaded:
                return True

            elif self.audio:
                return True
                
            elif self.image and self.image._coreimage.loaded:
                return True
        
    def on_show(self, fade_start, fade_end):
        self.media_sync()

        if self.video:
            self.video.state = 'play'
            self.client.source.add_widget(self.video, index = self.client.get_widget_index(self))
            
        elif self.audio:
            self.audio.play()
            
        elif self.image:
            self.client.source.add_widget(self.image, index = self.client.get_widget_index(self))
            
        if self.fade: self.fade.stop()
        self.fade = Fade(self.client.time, self.fade_val, 1, fade_start, fade_end, self.fade_tick, None)
        
    def on_hide(self, fade_start, fade_end):
        if self.fade: self.fade.stop()
        self.fade = Fade(self.client.time, self.fade_val, 0, fade_start, fade_end, self.fade_tick, self.fade_out_end)
