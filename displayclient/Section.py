import kivy
kivy.require('1.9.0')

from kivy.uix.widget import Widget
from kivy.graphics.vertex_instructions import Quad
from kivy.graphics.transformation import Matrix
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle, ClearBuffers, ClearColor

import numpy

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
