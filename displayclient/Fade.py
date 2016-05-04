from kivy.clock import Clock

class Fade:
    def __init__(self, time, start_val, end_val, start_time, end_time, fade_callback, end_callback):
        self.time = time

        self.start_val = start_val
        self.curr_val = start_val
        self.end_val = end_val
        
        self.start_time = start_time
        self.end_time = end_time

        self.length = self.end_time - self.start_time
        
        self.fade_callback = fade_callback
        self.end_callback = end_callback
                
        Clock.schedule_once(self.tick, 0)
        
    def stop(self):
        Clock.unschedule(self.tick)
        
    def tick(self, dt):
        curr_time = self.time.now()
        if curr_time < self.start_time: return
        
        elapsed = curr_time - self.start_time
        
        if self.curr_val < self.end_val:
            try: self.curr_val = self.start_val + (self.end_val - self.start_val) / (self.length / elapsed)
            except ZeroDivisionError: self.curr_val = self.end_val
            if self.curr_val > self.end_val: self.curr_val = self.end_val

        # TODO figure out why fades from 1 to 0 go up instead of down
        elif self.curr_val > self.end_val:
            try: self.curr_val = self.end_val + (self.start_val - self.end_val) / (self.length / (self.length - elapsed))
            except ZeroDivisionError: self.curr_val = self.end_val
            if self.curr_val < self.end_val: self.curr_val = self.end_val

        self.fade_callback(self.curr_val)
        
        if self.curr_val == self.end_val:
            if self.end_callback: self.end_callback()

        else:
            Clock.schedule_once(self.tick, 0)
