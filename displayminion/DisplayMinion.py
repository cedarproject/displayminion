import kivy
kivy.require('1.9.0')

import kivy.utils

from kivy.config import Config
Config.set('kivy', 'log_level', 'debug')

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import Color, Rectangle

import sys
import json
import time

from MeteorClient import MeteorClient

from .MeteorTime import MeteorTime
from .Section import Section
from .DisplaySource import DisplaySource
from .UserInterface import UserInterface

from .Action import Action
from .MediaAction import MediaAction
from .PlaylistAction import PlaylistAction
from .SongAction import SongAction
from .PresentationAction import PresentationAction
from .TimerAction import TimerAction

# TODO implement stuff from https://kivy.org/planet/2011/05/kivy-window-management-on-x11/ to make window fullscreen, optionally on multiple monitors

class DisplayMinion(App):
    action_map = {
        'media': MediaAction,
        'playlist': PlaylistAction,
        'song': SongAction,
        'presentation': PresentationAction,
        'presentationslide': PresentationAction,
        'timer': TimerAction,
        'clear-layer': Action
    }
    
    def __init__(self, **kwargs):
        self._id = None
        self.server = None
        self.ready = False

        self.state = 'disconnected' # 'disconnected' => 'connecting' => 'connected' => 'registering' => 'registered'
        self.binds = {}
        
        self.layers = {}

        self.sections = []
        self.last_blocks = None
        
        self.fullscreen = False
        
        self.defaults = json.load(open('common/default_settings.json'))
        
        super(DisplayMinion, self).__init__(**kwargs)

    def debug(self, *args):
        print(*args)
#        if self.config.get('debug'):
#            print(*args)

    def bind(self, event, function):
        if self.binds.get(event):
            self.binds[event].append(function)
            
        else:
            self.binds[event] = [function]
            
    def trigger_event(self, event):
        event_data = {'event': event, 'client': self}

        for function in self.binds.get(event, []):
            function(event_data)

    def connect(self, server):
        self.server = server
        
        self.meteor = MeteorClient('ws://{}/websocket'.format(self.server))
        self.meteor.on('connected', self.connected)
        self.meteor.connect()

        self.state = 'connecting'
        self.trigger_event('connecting')

    def connected(self):
        self.state = 'connected'
        self.trigger_event('connected')

        self.debug('Connected to server')

        self.time = MeteorTime(self.meteor)
        Clock.schedule_interval(self.time.update, 0.5)

        self.collections = 0
        self.collections_ready = 0

        for collection in ['settings', 'stages', 'minions',
                           'media', 'mediaplaylists',
                           'songs', 'songarrangements', 'songsections',
                           'presentations', 'presentationslides']:

            #TODO add all subscriptions
            self.collections += 1
            self.meteor.subscribe(collection, callback=self.subscription_ready)

    def subscription_ready(self, err):
        if err: self.debug(err)
        self.collections_ready += 1

        if self.collections_ready >= self.collections:
            self.trigger_event('loaded')
            self.debug('All subscriptions ready')

    def register(self, _id):
        self._id = _id
        self.meteor.call('minionConnect', [_id], self.prep)

        self.state = 'registering'
        self.trigger_event('registering')
        
    def prep(self, e, r):
        self.state = 'registered'
        self.trigger_event('registered')
    
        self.debug('Registered')
        
        self.meteor.on('added', self.added)
        self.meteor.on('changed', self.changed)
        
        self.minion = self.meteor.find_one('minions', selector = {'_id': self._id});
        self.stage = self.meteor.find_one('stages', selector = {'_id': self.minion['stage']})

        self.update_minion_settings(self.minion)

        Clock.create_trigger(self.update_layers)()
        Clock.schedule_once(self.update_minion_blocks, 0)
        
        self.ready = True
            
    def added(self, collection, _id, fields):
        self.changed(collection, _id, fields, None)
        
    def changed(self, collection, _id, fields, cleared):
        if not self.ready: return
        
        if collection == 'minions' and _id == self._id:
            self.minion = self.meteor.find_one('minions', selector = {'_id': self._id});
            self.update_minion_settings(self.minion)
        
        if collection == 'stages' and _id == self.minion['stage']:
            self.stage = self.meteor.find_one('stages', selector = {'_id': self.minion['stage']})
            Clock.create_trigger(self.update_layers)()
            
    def update_minion_settings(self, minion):
        if not minion['settings']['blocks'] == self.last_blocks:
            self.last_blocks = minion['settings']['blocks']
            Clock.schedule_once(self.update_minion_blocks, 0)
        
        if not minion['settings'].get('mediaminion_width', 0) == self.source.disp_size[0] or \
           not minion['settings'].get('mediaminion_height', 0) == self.source.disp_size[1]:
            self.source.disp_size = (int(minion['settings'].get('mediaminion_width') or 0), int(minion['settings'].get('mediaminion_height') or 0))
            self.source.resize()
        
    def update_minion_blocks(self, dt):
        # Note: Sections were originally named "blocks", so far I've been to lazy to rewrite all the cedarserver code to reflect the new name. -IHS
        start_length = len(self.sections)
        block_delta = len(self.minion['settings']['blocks']) - start_length

        if block_delta > 0:
            for n in range(block_delta):
                config = self.minion['settings']['blocks'][start_length + n]
                
                section = Section(
                    source = self.source,
                    block = config,
                    client = self
                )
                
                self.layout.add_widget(section)
                self.sections.append(section)
                
        elif block_delta < 0:
            for n in range(abs(block_delta)):
                section = self.sections.pop()
                self.layout.remove_widget(section)
        
        for index, section in enumerate(self.sections):
            config = self.minion['settings']['blocks'][index]
            if not section.block == config: # TODO add brightness etc.
                section.block = config
                section.recalc()
    
    def update_layers(self, dt = None):
        layers = self.stage.get('layers', [])

        for layer, action in layers.items():
            if not layer in self.minion['layers']: continue
        
            if action and self.layers.get(layer):
                # Test if new action is the same as the current one
                current = self.layers.get(layer).action

                if action['_id'] == current['_id']:
                    if action['type'] == 'song':
                        if action.get('args') and current.get('args') and \
                           action['args']['section'] == current['args']['section'] and \
                           action['args']['index'] == current['args']['index']:
                            continue
                    
                    elif action['type'] == 'presentation':
                        if action.get('args') and current.get('args') and \
                           action['args']['order'] == current['args']['order'] and \
                           action['args']['fillin'] == current['args']['fillin']:
                            continue
                            
                    else: continue
            
            if action and self.action_map.get(action['type']):
                self.layers[layer] = self.action_map[action['type']](action, self.layers.get(layer) or None, self)
                self.layers[layer].show()
                
            elif action == None and self.layers.get(layer):
                self.layers[layer].hide()
                self.layers[layer].remove()
                self.layers[layer] = None
            
                
    def get_layer_index(self, target_layer):
        layers = self.stage['settings']['layers']
        layer_index = layers.index(target_layer)

        higher_layers = layers[layer_index + 1:]
        widget_index = 0

        for layer in higher_layers:
            higher_action = self.layers.get(layer)
 
            if higher_action:
                higher_index = higher_action.get_current_widget_index()
                
                if not higher_index == None:
                    widget_index = higher_index + 1
                    break
                
        return widget_index
        

    def add_layer_widget(self, new_widget, layer):
        # TODO switch to this behavior once https://github.com/kivy/kivy/issues/4293 is resolved
        # self.source.add_widget(widget, index = self.get_layer_index(layer))
        
        widgets = self.source.children[:]
        new_index = self.get_layer_index(layer)
        
        for widget in widgets:
            self.source.remove_widget(widget)
        
        widgets.insert(new_index, new_widget)
        widgets.reverse()
        
        for widget in widgets:
            self.source.add_widget(widget)

    
    def remove_widget(self, widget):
        self.source.remove_widget(widget)

    def get_application_config(self):
        return super(DisplayMinion, self).get_application_config('~/.%(appname)s.ini')

    def build_config(self, config):
        config.setdefaults('connection', {
            'server': 'localhost:3000',
            '_id': '',
            'autoconnect': 'no'
        })
   
    def toggle_fullscreen(self, *args, **kwargs):
        print('toggle?')
        if self.fullscreen: Window.fullscreen = 0
        else: Window.fullscreen = 'auto'
        self.fullscreen = not self.fullscreen
        
    def build(self):
        self.title = 'Cedar Display Client'
        
        if kivy.utils.platform is 'windows':
            self.icon = 'logo/logo-128x128.png'
        else:
            self.icon = 'logo/logo-1024x1024.png'

        self.source = DisplaySource(self, pos_hint = {'x': 1, 'y': 1}, size_hint = [None, None])

        self.layout = FloatLayout()
        self.layout.add_widget(self.source)
        
        self.layout.bind(on_touch_down = self.toggle_fullscreen)
        
        self.ui = UserInterface(self)
        
        return self.layout

