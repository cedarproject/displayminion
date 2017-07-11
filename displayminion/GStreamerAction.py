from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from ctypes import Structure, c_void_p, c_int, string_at

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

Gst.init(None)

from .Action import Action

class _MapInfo(Structure):
    _fields_ = [
        ('memory', c_void_p),
        ('flags', c_int),
        ('data', c_void_p)]

class GStreamerAction(Action):
    def __init__(self, *args, **kwargs):
        super(GStreamerAction, self).__init__(*args, **kwargs)

        self.settings = self.combine_settings(self.settings, self.client.minion.get('settings'), self.action.get('settings'))
        
        self.fade_length = self.settings.get('media_fade')
        self.input_pipeline = self.settings.get('camera_pipeline')
        
        try:
            self.resolution = (
                int(self.settings.get('camera_width')),
                int(self.settings.get('camera_height'))
            )
        except ValueError:
            self.resolution = Window.size

        self.texture = Texture.create(size = self.resolution, colorfmt = 'rgb')
        self.texture.flip_vertical()
        
        self.image = Image(texture = self.texture)
        
        if self.settings.get('media_preserve_aspect') == 'no':
            self.image.keep_ratio = False

        self.image.opacity = 0
        
        caps = 'video/x-raw,format=RGB,width={},height={}'.format(*self.resolution)
        pl = '{} ! videoconvert ! videoscale ! appsink name=appsink emit-signals=True caps={}'
        
        self.pipeline = Gst.parse_launch(pl.format(self.input_pipeline, caps))
        self.appsink = self.pipeline.get_by_name('appsink')
        self.appsink.connect('new-sample', self.new_sample)
    
        self.pipeline.set_state(Gst.State.READY)

    def new_sample(self, *args):
        sample = self.appsink.emit('pull-sample')
        if sample is None:
            return False

        self.sample = sample

        Clock.schedule_once(self.update)
        return False

    def update(self, dt):
        sample, self.sample = self.sample, None
        if sample is None:
            return

        try:
            buf = sample.get_buffer()
            result, mapinfo = buf.map(Gst.MapFlags.READ)

            addr = mapinfo.__hash__()
            c_mapinfo = _MapInfo.from_address(addr)

            sbuf = string_at(c_mapinfo.data, mapinfo.size)
            self.texture.blit_buffer(sbuf, colorfmt = 'rgb')
        finally:
            if mapinfo is not None:
                buf.unmap(mapinfo)
        
        self.image.canvas.ask_update()

    def get_current_widget_index(self):
        if self.shown:
            return self.client.source.children.index(self.image)
        
    def out_animation_end(self):
        self.pipeline.set_state(Gst.State.NULL)

        self.shown = False
        self.client.remove_widget(self.image)
        
    def on_show(self, fade_length):
        self.pipeline.set_state(Gst.State.PLAYING)

        self.client.add_layer_widget(self.image, self.layer)
        self.add_anim_widget(self.image, 'opacity', 1, 0)
        
        self.do_in_animation(fade_length)
            
    def on_hide(self, fade_length):
        self.do_out_animation(fade_length)

