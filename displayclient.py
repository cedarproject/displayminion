import kivy
kivy.require('1.9.0')

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.video import Video
from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics.vertex_instructions import Quad
from kivy.graphics.transformation import Matrix
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle, ClearBuffers, ClearColor

import sys
import json
import time

from MeteorClient import MeteorClient

from displayclient import MeteorTime
from displayclient import MediaAction
from displayclient import Section, DisplaySource
        
class DisplayClient(App):
    action_map = {
        'media': MediaAction
    }
    
    def __init__(self, **kwargs):
        self.server = 'localhost:3000'
        self.meteor = MeteorClient('ws://{}/websocket'.format(self.server))
        self.meteor.on('connected', self.connected)
        self.meteor.connect()
        
        self.layers = {}

        self.sections = []
        self.last_blocks = None
        self.sections_changed = False
        
        self.time = MeteorTime(self.meteor)
    
        super(DisplayClient, self).__init__(**kwargs)

    def debug(self, *args):
        print(*args)
#        if self.config.get('debug'):
#            print(*args)

    def connected(self):
        self.debug('Connected to server')

        Clock.schedule_interval(self.time.update, 0.5)

        self._id = 'HTKBTN8i2SNQXftd4'
        self.register(None, self._id)

    def register(self, err, _id):
        self.meteor.call('minionConnect', [_id], self.prep)
        
    def prep(self, e, r):
        self.debug('Registered')
        
        self.collections = 0
        self.collections_ready = 0
        self.ready = False

        for collection in ['settings', 'stages', 'minions', 'media']:
            #TODO add all subscriptions
            self.collections += 1
            self.meteor.subscribe(collection, callback=self.subscription_ready)

        self.meteor.on('added', self.added)
        self.meteor.on('changed', self.changed)
        
    def subscription_ready(self, err):
        if err: self.debug(err)
        self.collections_ready += 1

        if self.collections_ready >= self.collections:
            self.debug('All subscriptions ready')
            self.minion = self.meteor.find_one('minions', selector={'_id': self._id});
            self.update_minion_settings(self.minion)

            self.ready = True
            
            self.stage = self.meteor.find_one('stages', selector={'_id': self.minion['stage']})
            Clock.create_trigger(self.update_layers)()
            
    def added(self, collection, _id, fields):
        self.changed(collection, _id, fields, None)
        
    def changed(self, collection, _id, fields, cleared):
        if not self.ready: return
        
        if collection == 'minions' and _id == self._id:
            self.minion = self.meteor.find_one('minions', selector={'_id': self._id});
            self.update_minion_settings(self.minion)
        
        if collection == 'stages' and _id == self.minion['stage']:
            self.stage = self.meteor.find_one('stages', selector={'_id': self.minion['stage']})
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
                self.layout.remove_widget(section)
        
        for index, section in enumerate(self.sections):
            config = self.minion['settings']['blocks'][index]
            if not section.points == config['points']: # TODO add brightness etc.
                section.points = config['points']
                section.recalc()
    
    def update_layers(self, dt = None):
        layers = self.stage.get('layers', [])

        for layer, action in layers.items():
            if action and self.action_map.get(action['type']):
                self.layers[layer] = self.action_map[action['type']](action, self.layers.get(layer) or None, self)
                self.layers[layer].show()
                
            elif action == None and self.layers.get(layer):
                self.layers[layer].hide()
                self.layers[layer].remove()
                
    def build(self):
        self.source = DisplaySource(pos=Window.size)
        self.layout = FloatLayout()
        self.layout.add_widget(self.source)
        
        Clock.schedule_interval(self.update_minion_blocks, 0.1)
        
        return self.layout
                    
if __name__ == '__main__':
    DisplayClient().run()
