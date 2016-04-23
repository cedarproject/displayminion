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
import numpy

from MeteorClient import MeteorClient

class MeteorTime:
    def __init__(self, meteor):
        self.meteor = meteor
        
        self.latency = 0
        self.last = 0
        self.last_time = 0
    
    def update(self):
        self.start = time.time()
        self.meteor.call('getTime', [], self.callback)
        
    def callback(self, error, server_now):
        now = time.time()
        self.latency = now - self.start
        self.last = (server_now - self.latency / 2) * 0.001
        self.last_time = now
        
    def now(self):
        return (self.last + (time.time() - self.last_time)) * 1000
        
class DisplaySource(FloatLayout):
    texture = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.canvas = RenderContext(use_parent_projection=True)

        with self.canvas:
            self.fbo = Fbo(size=Window.size, use_parent_projection=True)

        super(DisplaySource, self).__init__(**kwargs)        
            
        self.canvas.shader.fs = open(resource_find('source.glsl')).read()

        self.texture = self.fbo.texture
        Clock.schedule_interval(self.update_glsl, 0)
        
    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = [float(v) for v in self.size]
        
    def add_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(DisplaySource, self).add_widget(widget)
        self.canvas = c

    def remove_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(DisplaySource, self).remove_widget(widget)
        self.canvas = c
        
class Section(Widget):
    source = ObjectProperty(None)
    points = ListProperty(None)

    def __init__(self, **kwargs):
        self.canvas = RenderContext(use_parent_projection=True)

        super(Section, self).__init__(**kwargs)

        self.canvas.shader.fs = open(resource_find('section_fragment.glsl')).read()
        self.canvas.shader.vs = open(resource_find('section_vertex.glsl')).read()

        s = Window.size

        before = [
            [-1, -1],
            [1, -1],
            [1, 1],
            [-1, 1]
        ]
        
        after = numpy.array(self.points)
        
        A = []
        for a, b in zip(after, before):
            A.append([
                b[0], 0, -a[0] * b[0],
                b[1], 0, -a[0] * b[1], 1, 0]);
            A.append([
                0, b[0], -a[1] * b[0],
                0, b[1], -a[1] * b[1], 0, 1]);
                                

        A = numpy.array(A)

        B = numpy.array([[c for p in self.points for c in p]])
        B = B.transpose()

        m = numpy.dot(numpy.linalg.inv(A), B)

        m = m.transpose().reshape(-1,).tolist()
                
        matrix = Matrix()
        matrix.set([
            m[0], m[1],   0, m[2],
            m[3], m[4],   0, m[5],
               0,    0,   1,    0,
            m[6], m[7],   0,    1
        ])
                
        self.canvas['uTransformMatrix'] = matrix

        quad_points = [c for p in before for c in [p[0] , p[1]]] # Bwa ha ha.

        with self.canvas:
            Quad(texture = self.source.texture, points = quad_points)
        
class DisplayClient(App):
    def __init__(self, **kwargs):
        self.server = 'localhost:3000'
        self.meteor = MeteorClient('ws://{}/websocket'.format(self.server))
        self.meteor.on('connected', self.connected)
        self.meteor.connect()
    
        super(DisplayClient, self).__init__(**kwargs)

    def debug(self, *args):
        print(*args)
#        if self.config.get('debug'):
#            print(*args)

    def connected(self):
        self.debug('Connected to server')
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
            self.ready = True
            
            stage = self.meteor.find_one('stages', selector={'_id': self.minion['stage']})
            self.update_layers(stage)
            

    def added(self, collection, _id, fields):
        self.changed(collection, _id, fields, None)
        
    def changed(self, collection, _id, fields, cleared):
        if not self.ready: return
        
        if collection == 'minions' and _id == self._id:
            self.minion = self.meteor.find_one('minions', selector={'_id': self._id});
            # TODO also update Sections, etc.
        
        if collection == 'stages' and _id == self.minion['stage']:
            stage = self.meteor.find_one('stages', selector={'_id': self.minion['stage']})
            self.update_layers(stage)
    
    def update_layers(self, stage):
        layers = stage.get('layers', [])

        for layer, action in layers.items():
            if action and action.get('type') == 'media' and action.get('mediatype') == 'video':
                # TODO make this separate class
                media = self.meteor.find_one('media', selector={'_id': action.get('media')})
                mediaurl = self.meteor.find_one('settings', selector={'key': 'mediaurl'})['value']
                source = 'http://{}{}'.format(self.server, mediaurl + media['location'])

                video = Video(source = source, play = True)
                video.allow_stretch = True
                video.keep_ratio = True
                self.source.add_widget(video)        
                    

    def build(self):
        self.source = DisplaySource(pos=Window.size)
                    
        self.layout = FloatLayout()
        
        self.section_1 = Section(
            source = self.source,
            points = [
                [0.25, 0],
                [1, 0],
                [1, 0.75],
                [0, 1]
            ]
        )

        self.section_2 = Section(
            source = self.source,
            points = [
                [-1, -1],
                [0, -1],
                [0, 0],
                [-1, 0]
            ]
        )
        
        self.layout.add_widget(self.source)
        self.layout.add_widget(self.section_1)
        self.layout.add_widget(self.section_2)
        
        return self.layout
                    
if __name__ == '__main__':
    DisplayClient().run()
