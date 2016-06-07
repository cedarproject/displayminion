import kivy
kivy.require('1.9.0')

from kivy.uix.widget import Widget
from kivy.graphics.vertex_instructions import Quad
from kivy.graphics.transformation import Matrix
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty, BooleanProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle, ClearBuffers, ClearColor

import numpy

class Section(Widget):
    source = ObjectProperty(None)
    block = ObjectProperty(None)

    def __init__(self, client, **kwargs):
        self.canvas = RenderContext(use_parent_projection=True)
        self.client = client

        super(Section, self).__init__(**kwargs)

        self.source.sections.append(self)

        self.canvas.shader.fs = open(resource_find('shaders/section_fragment.glsl')).read()
        self.canvas.shader.vs = open(resource_find('shaders/section_vertex.glsl')).read()
        
        Window.bind(on_resize = self.recalc)
        
        self.recalc()
    
    def recalc(self, *args, **kwargs):
        w, h = self.source.texture.width, self.source.texture.height

        self.texture = self.source.texture.get_region(
            min(self.block['x'] * w, w),
            min(self.block['y'] * h, h),
            min(self.block['width'] * w, w),
            min(self.block['height'] * h, h)
        )
        
        before = [
            [-1, -1],
            [1, -1],
            [1, 1],
            [-1, 1]
        ]
        
        after = numpy.array(self.block['points'])
        
        A = []
        for a, b in zip(after, before):
            A.append([
                b[0], 0, -a[0] * b[0],
                b[1], 0, -a[0] * b[1], 1, 0]);
            A.append([
                0, b[0], -a[1] * b[0],
                0, b[1], -a[1] * b[1], 0, 1]);
                                
        A = numpy.array(A)

        B = numpy.array([[c for p in self.block['points'] for c in p]])
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
        self.canvas['brightness'] = float(self.block.get('brightness', 1))
        self.canvas['alpha_mask'] = int(self.block.get('alpha_mask', False)) # Because Kivy can't pass booleans to shaders, apparently.
        self.canvas['adjust'] = float(self.client.minion['settings'].get('displayminion_color_adjust_range', 0))
        
#        self.canvas['blend_top'] = float(self.block['blend_top'])
#        self.canvas['blend_bottom'] = float(self.block['blend_bottom'])
#        self.canvas['blend_left'] = float(self.block['blend_left'])
#        self.canvas['blend_right'] = float(self.block['blend_right'])

        self.canvas.clear()
        with self.canvas:
            self.rect = Rectangle(texture = self.texture, size = (2, 2), pos = (-1, -1))
