from kivy.clock import Clock

import math

from .Action import Action
from .MediaAction import MediaAction

class PlaylistAction(Action):
    def __init__(self, *args, **kwargs):
        super(PlaylistAction, self).__init__(*args, **kwargs)
        
        self.playlist = self.meteor.find_one('mediaplaylists', selector = {'_id': self.action['playlist']})
        self.settings = self.combine_settings(self.settings, self.client.minion.get('settings'), self.playlist.get('settings'), self.action.get('settings'))
        
        self.fade_length = float(self.settings.get('media_fade'))
        
        # The settings dict is passed to child MediaActions, so looping is disabled.
        self.playlist_loop = self.settings.get('media_loop')
        self.settings['media_loop'] = False
        
        if self.settings.get('playlist_order') == 'normal':
            self.order = self.playlist['contents']
        elif self.settings.get('playlist_order') == 'random':
            self.order = []
            contents = self.playlist['contents'][:]
            
            for i in range(len(contents)):
                x = math.sin(self.action['time'] + i) * 10000;
                r = x - math.floor(x);
                self.order.append(contents.pop(math.floor(r * len(contents))))
                
        self.index = 0
        self.current = None
        self.current_time = self.action['time']
                    
    def next(self, dt = None):
        if self.shown:
            if self.index <= len(self.order) - 1:
                new_action = {
                    'media': self.order[self.index],
                    'settings': self.settings,
                    'layer': self.layer,
                    'time': self.current_time
                }
                
                self.current = MediaAction(new_action, self.current, self.client)
                self.current.show()
                
                if self.current.media['type'] == 'image':
                    delay = float(self.settings.get('playlist_image_length')) - self.fade_length
                else:
                    delay = float(self.current.media['duration']) - self.fade_length
                    
                if delay < 0: delay = 0 # In case fade length is ever greater than media duration
                
                Clock.schedule_once(self.next, self.current_time - self.time.now() + delay)
                
                self.current_time += delay
                
                self.index += 1
                
            
            elif self.playlist_loop:
                self.index = 0
                self.next()
            
            else:
                if self.current: self.current.hide()
    
    def get_current_widget_index(self):
        if self.current: return self.current.get_current_widget_index()
        
    def on_show(self, fade_start, fade_end):
        self.shown = True

        # If the playlist's start is in the past, determine where in the playlist to skip to.
        # TODO figure out a more efficient way to code this, currently it's pretty inefficient
        if self.time.now() > self.current_time:
            while True:
                media = self.meteor.find_one('media', selector = {'_id': self.order[self.index]})
                
                if media['type'] == 'image':
                    duration = float(self.settings.get('playlist_image_length')) - self.fade_length
                else:
                    duration = float(media['duration']) - self.fade_length                
                
                if self.time.now() < self.current_time + duration:
                    break
                else:
                    self.current_time += duration
                    self.index += 1
                    
                    if self.index >= len(self.order):
                        if self.playlist_loop: self.index = 0
                        else: break

        self.next()
        
    def on_hide(self, fade_start, fade_end):
        self.current.hide()
        self.current.remove()

        self.shown = False
