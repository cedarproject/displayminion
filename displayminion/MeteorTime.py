import time

class MeteorTime:
    def __init__(self, meteor):
        self.meteor = meteor
        
        self.latency = 0
        self.last = 0
        self.last_time = 0
    
    def update(self, dt):
        self.start = time.time()
        self.meteor.call('getTime', [], self.callback)
        
    def callback(self, error, server_now):
        # TODO set maximum value for adjustment to smooth out changes
        now = time.time()
        self.latency = now - self.start
        self.last = (server_now - self.latency / 2) * 0.001
        self.last_time = now
        
    def now(self):
        return self.last + (time.time() - self.last_time)
