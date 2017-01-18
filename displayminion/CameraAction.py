from kivy.uix.camera import Camera

from .Action import Action

class CameraAction(Action):
    def __init__(self, *args, **kwargs):
        super(CameraAction, self).__init__(*args, **kwargs)

        self.settings = self.combine_settings(self.settings, self.client.minion.get('settings'), self.action.get('settings'))
        
        self.fade_length = self.settings.get('media_fade')
        self.camera_index = self.settings.get('camera_index')
        
        try:
            self.resolution = (
                int(self.settings.get('camera_width')),
                int(self.settings.get('camera_height'))
            )
        except ValueError:
            self.resolution = (0, 0)
        
        try:
            self.camera = Camera(index = self.camera_index, resolution = self.resolution)
        except Exception as e:
            print('Error initializing camera:', e)
            self.camera = None
            return

        if self.settings.get('media_preserve_aspect') == 'no':
            self.camera.keep_ratio = False

        self.camera.opacity = 0

    def get_current_widget_index(self):
        if self.shown and self.camera:
            return self.client.source.children.index(self.camera)
        
    def out_animation_end(self):
        if self.camera:
            self.camera.play = False

            self.shown = False
            self.client.remove_widget(self.camera)
        
    def on_show(self, fade_length):
        if self.camera:
            self.camera.play = True

            self.client.add_layer_widget(self.camera, self.layer)
            self.add_anim_widget(self.camera, 'opacity', 1, 0)
            
            self.do_in_animation(fade_length)
            
    def on_hide(self, fade_length):
        self.do_out_animation(fade_length)

