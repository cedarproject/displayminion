from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label

class UserInterface:
    def __init__(self, client):
        # TODO handle connection errors properly
        self.client = client
        self.layout = GridLayout(cols = 2, pos_hint={'x': 0, 'y': 0}, size_hint=(1, 0.1))
        self.client.layout.add_widget(self.layout, index = 1000)
        
        self.client.bind('connected', self.connected)
        self.client.bind('loaded', self.loaded)
        self.client.bind('registered', self.registered)
        
        if self.client.config.get('connection', 'autoconnect') == 'yes':
            self.auto = True
            self.client.connect(self.client.config.get('connection', 'server'))
        else:
            self.auto = False
        
            self.server_input = TextInput(text = self.client.config.get('connection', 'server'))
            self.server_button = Button(text = 'Connect', size_hint = (0.25, 1))
            self.server_button.bind(on_press = self.do_connect)
            
            self.layout.add_widget(self.server_input)
            self.layout.add_widget(self.server_button)
        
    def do_connect(self, button):
        self.client.connect(self.server_input.text)
        
        self.layout.remove_widget(self.server_input)
        self.layout.remove_widget(self.server_button)
        del self.server_input, self.server_button
        
        self.connecting_label = Label(text = 'connecting...')
        self.layout.add_widget(self.connecting_label)
        
    def connected(self, event):
        if not self.auto:
            self.client.config.set('connection', 'server', self.client.server)
            self.connecting_label.text = 'loading...'
        
    def loaded(self, event):
        if self.auto:
            self.client.register(self.client.config.get('connection', '_id'))
            return
        
        self.layout.remove_widget(self.connecting_label)
        del self.connecting_label
        
        self.dropdown = DropDown()
        
        for stage in sorted(self.client.meteor.find('stages'), key=lambda x: x['title']):
            self.dropdown.add_widget(Label(text = stage['title'], size_hint_y = None, height = 40))
            
            seen = []
            for minion in sorted(self.client.meteor.find('minions', 
                    selector = {'stage': stage['_id'], 'type': 'media'}), key=lambda x: x['title']):
                # workaround for python-meteor bug
                if not minion['stage'] == stage['_id']: continue
                
                if minion['_id'] in seen: continue
                else: seen.append(minion['_id'])

                button = Button(text = minion['title'], size_hint_y = None, height = 30)
                button.minion_id = minion['_id']
                button.bind(on_press = self.do_register)
                self.dropdown.add_widget(button)
        
        self.dropdown_button = Button(text = 'Select Minion')
        self.dropdown_button.bind(on_release = self.dropdown.open)
        self.layout.add_widget(self.dropdown_button)
            
        self.auto_checkbox = CheckBox()
        self.auto_label = Label(text = 'Connect automatically on start')
        self.layout.add_widget(self.auto_checkbox)
        self.layout.add_widget(self.auto_label)        
        
    def do_register(self, button):
        self.client.config.set('connection', '_id', button.minion_id)
        self.client.config.set('connection', 'autoconnect', 'yes' if self.auto_checkbox.active else 'no')
        self.client.config.write()
        self.client.register(button.minion_id)
        
        self.dropdown.dismiss()
        self.layout.remove_widget(self.dropdown_button)
        self.layout.remove_widget(self.auto_checkbox)
        self.layout.remove_widget(self.auto_label)
        del self.dropdown_button, self.dropdown, self.auto_checkbox, self.auto_label
        
        self.registering_label = Label(text = 'registering...')
        self.layout.add_widget(self.registering_label)
        
    def registered(self, event):
        if not self.auto:
            self.layout.remove_widget(self.registering_label)
            del self.registering_label
