import kivy
kivy.require('1.9.0')

from kivy.uix.widget import Widget
from kivy.graphics.vertex_instructions import Quad
from kivy.graphics.transformation import Matrix
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty, BooleanProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle, ClearBuffers, ClearColor

from kivy.core.window import Window

import copy
import numpy

class Section(Widget):
    source = ObjectProperty(None)
    block = ObjectProperty(None)

    def __init__(self, client, **kwargs):
        self.canvas = RenderContext(use_parent_projection=True)
        self.client = client

        super(Section, self).__init__(**kwargs)
        
        self.canvas.shader.fs = open(resource_find('shaders/section_fragment.glsl')).read()
        self.canvas.shader.vs = open(resource_find('shaders/section_vertex.glsl')).read()
        
        self.recalc()
    
    def recalc(self, *args, **kwargs):
        block = copy.deepcopy(self.block)
        
        block['x'] -= block['blend_left'] / 2
        block['y'] -= block['blend_top'] / 2
        block['width'] += block['blend_left'] / 2 + block['blend_right'] / 2
        block['height'] += block['blend_top'] / 2 + block['blend_bottom'] / 2
        
        print(block['x'], block['y'], block['width'], block['height'])
        
        if block['x'] < 0: block['x'] = 0
        if block['y'] < 0: block['x'] = 0
        if block['width'] > 1: block['width'] = 1
        if block['height'] > 1: block['height'] = 1
    
        w, h = self.source.texture.width, self.source.texture.height
        sw, sh = self.source.width / self.source.texture.width, self.source.height / self.source.texture.height

#        self.texture = self.source.texture.get_region(
#            sw * min(block['x'] * w, w) - (block['blend_left'] * w / 2),
#            sh * min(block['y'] * h, h) - (block['blend_top'] * h / 2),
#            sw * min(block['width'] * w, w) + (block['blend_right'] * w / 2),
#            sh * min(block['height'] * h, h) + (block['blend_bottom'] * h / 2)
#        )

        self.texture = self.source.texture.get_region(
            sw * min(block['x'] * w, w),
            sh * min(block['y'] * h, h),
            sw * min(block['width'] * w, w),
            sh * min(block['height'] * h, h)
        )
                          
        before = [
            [-1, -1],
            [1, -1],
            [1, 1],
            [-1, 1]
        ]
        
        # Adjust size of section if edge blending is used
        points = block['points']
        points[3] = [points[3][0] - block['blend_left'], points[3][1] + block['blend_bottom']]
        points[2] = [points[2][0] + block['blend_right'], points[2][1] + block['blend_bottom']]
        points[0] = [points[0][0] - block['blend_left'], points[0][1] - block['blend_top']]
        points[1] = [points[1][0] + block['blend_right'], points[1][1] - block['blend_top']]

        after = numpy.array(points)
        
        A = []
        for a, b in zip(after, before):
            A.append([
                b[0], 0, -a[0] * b[0],
                b[1], 0, -a[0] * b[1], 1, 0]);
            A.append([
                0, b[0], -a[1] * b[0],
                0, b[1], -a[1] * b[1], 0, 1]);
                                
        A = numpy.array(A)

        B = numpy.array([[c for p in block['points'] for c in p]])
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

        self.canvas['brightness'] = float(block.get('brightness', 1))
        self.canvas['alpha_mask'] = int(block.get('alpha_mask', False)) # Because Kivy can't pass booleans to shaders, apparently.
        self.canvas['adjust'] = float(self.client.minion['settings'].get('displayminion_color_adjust_range', 0))

        self.canvas['tex_x'] = block['x']
        self.canvas['tex_y'] = block['y']
        self.canvas['tex_width'] = block['width']
        self.canvas['tex_height'] = block['height']
        
        self.canvas['blend_top'] = float(block['blend_top'])
        self.canvas['blend_bottom'] = float(block['blend_bottom'])
        self.canvas['blend_left'] = float(block['blend_left'])
        self.canvas['blend_right'] = float(block['blend_right'])
        
        self.canvas.clear()
        with self.canvas:
            self.rect = Rectangle(texture = self.texture, size = (2, 2), pos = (-1, -1))
