media_sync_interval = 0.25
media_sync_tolerance = 0.1

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.image import AsyncImage
from kivy.uix.video import Video
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle

from kivy.uix.label import Label

from .Action import Action
from .Fade import Fade

import urllib.parse

class MediaAction(Action):
    def __init__(self, *args, **kwargs):
        super(MediaAction, self).__init__(*args, **kwargs)

        self.media = self.meteor.find_one('media', selector={'_id': self.action.get('media')})

        self.duration = self.media.get('duration')
        if self.duration: self.duration = float(self.duration)
        else: self.duration = 0
        
        self.settings = self.combine_settings(self.settings, self.client.minion.get('settings'), self.media.get('settings'), self.action.get('settings'))
        
        self.fade_length = float(self.settings.get('media_fade'))
        self.fade_val = 0
        
        self.max_volume = min(float(self.settings.get('media_volume')), 1.0)
        self.minion_volume = min(float(self.settings.get('mediaminion_volume')), 1.0)
        
        # TODO autodetect HTTP/HTTPS, other protocols?
        mediaurl = self.meteor.find_one('settings', selector={'key': 'mediaurl'})['value']
        self.sourceurl = 'http://{}{}'.format(self.client.server, urllib.parse.quote(mediaurl + self.media['location']))
        
        self.video = None
        self.audio = None
        self.image = None
        
        self.to_sync = None
        
        if self.media['type'] == 'video':
            options = {}
            if self.settings.get('media_loop') == 'yes':
                options['eos'] = 'loop'

            self.video = Video(source = self.sourceurl, options = options, size = self.client.source.child_size, size_hint = (None, None))
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

            if self.settings.get('media_loop') == 'yes':
                self.audio.loop = True

            self.audio.volume = 0
        
        elif self.media['type'] == 'image':
            print('source size', self.client.source.size)
            self.image = AsyncImage(source = self.sourceurl, size = self.client.source.child_size, size_hint = (None, None))
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
        
        return diff
    
    def get_seek_percent(self, time):
        if time == 0: return 0
        else: return 1 / (self.media['duration'] / time)
        
    def media_sync(self, dt = None):
        if self.shown and not self.media['type'] == 'image':
            if self.video: pos = self.video.position
            elif self.audio: pos = self.audio.get_pos()
                
            if self.to_sync and abs(self.get_media_time() - pos) > media_sync_tolerance:
                if self.settings.get('media_loop') == 'no' and pos > self.duration:
                    if self.video: self.to_sync.state = 'stop'
                    elif self.audio: self.audio.stop()
                else:
                    print(self.media['title'], 'seeking to', self.get_media_time())
                    self.to_sync.seek(self.get_seek_percent(self.get_media_time()))
            
            # Automatic sync disabled until Kivy playback rate change is implemented
            #Clock.schedule_once(self.media_sync, media_sync_interval)
            
    def fade_tick(self, val):
        self.fade_val = val

        if self.video:
            self.video.opacity = val
            self.video.volume = val * self.max_volume * self.minion_volume

        elif self.audio:
            self.audio.volume = val * self.max_volume * self.minion_volume
            
        elif self.image:
            self.image.opacity = val
        
    def fade_out_end(self):
        self.shown = False
        
        if self.video:
            self.video.state = 'pause'
            self.client.remove_widget(self.video)

        elif self.audio:
            self.audio.stop()

        elif self.image:
            self.client.remove_widget(self.image)
        
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
            self.client.add_layer_widget(self.video, self.layer)
            
        elif self.audio:
            self.audio.play()
            
        elif self.image:
            self.client.add_layer_widget(self.image, self.layer)
            
        if self.fade: self.fade.stop()
        self.fade = Fade(self.client.time, self.fade_val, 1, fade_start, fade_end, self.fade_tick, None)
        
    def on_hide(self, fade_start, fade_end):
        if self.fade: self.fade.stop()
        self.fade = Fade(self.client.time, self.fade_val, 0, fade_start, fade_end, self.fade_tick, self.fade_out_end)
