import kivy
kivy.require('1.9.0')

from kivy.config import Config
Config.set('kivy', 'log_level', 'none')

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
from .SongAction import SongAction

class DisplayClient(App):
    action_map = {
        'media': MediaAction,
        'song': SongAction,
        'clear-layer': Action
    }
    
    def __init__(self, **kwargs):
        self._id = None
        self.server = 'localhost:3000'
        self.ready = False

        self.state = 'disconnected' # 'disconnected' => 'connecting' => 'connected' => 'registering' => 'registered'
        self.binds = {}
        
        self.layers = {}

        self.sections = []
        self.last_blocks = None
        self.sections_changed = False
        
        super(DisplayClient, self).__init__(**kwargs)

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

        for collection in ['settings', 'stages', 'minions', 'media', 'songs', 'songarrangements', 'songsections']:
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
        Clock.schedule_interval(self.update_minion_blocks, 0.1)
        
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
            self.sections_changed = True
        
    def update_minion_blocks(self, dt):
        if not self.sections_changed: return
        self.sections_changed = False
    
        # Note: Sections were originally named "blocks", so far I've been to lazy to rewrite all the cedarserver code to reflect the new name. -IHS
        start_length = len(self.sections)
        block_delta = len(self.minion['settings']['blocks']) - start_length

        if block_delta > 0:
            for n in range(block_delta):
                config = self.minion['settings']['blocks'][start_length + n]
                
                section = Section(
                    source = self.source,
                    points = config['points']
                    # TODO add brightess/width/height/x/y
                )
                
                self.layout.add_widget(section)
                self.sections.append(section)
                
        elif block_delta < 0:
            for n in range(abs(block_delta)):
                section = self.sections.pop()
                section.source.sections.remove(section)
                self.layout.remove_widget(section)
        
        for index, section in enumerate(self.sections):
            config = self.minion['settings']['blocks'][index]
            if not section.points == config['points']: # TODO add brightness etc.
                section.points = config['points']
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
                            print(action['args'], current['args'])
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
                
    def get_widget_index(self, action):
        layers = self.stage['settings']['layers']
        layer_index = layers.index(action.layer)

        higher_layers = layers[layer_index + 1:]
        widget_index = 0

        for layer in higher_layers:
            higher_action = self.layers.get(layer)
 
            if higher_action:
                higher_index = higher_action.get_current_widget_index()
                
                if not higher_index == None:
                    print(higher_index, self.source.children)
                    widget_index = higher_index + 1
                    break
                
        return widget_index
        
    def build(self):
        self.source = DisplaySource(pos=Window.size)

        self.layout = FloatLayout()
        self.layout.add_widget(self.source)
        
        self.ui = UserInterface(self)
        
        return self.layout

