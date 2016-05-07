import time

class MeteorTime:
    def __init__(self, meteor):
        self.meteor = meteor
        
        self.latency = 0
        self.last = 0
        self.last_time = 0
        
#        self.debug_start = None
#        self.debug_avg = 0
    
    def update(self, dt):
        self.start = time.time()
        self.meteor.call('getTime', [], self.callback)
        
    def callback(self, error, server_now):
        # TODO set maximum value for adjustment to smooth out changes
        now = time.time()
        self.latency = now - self.start
        self.last = (server_now - self.latency / 2) * 0.001
        self.last_time = now

        # TODO delete this once I'm sure MeteorTime is low-jitter        
#        if not self.debug_start: self.debug_start = now
#        diff = (self.now() - self.debug_start) - (time.time() - self.debug_start)
#        self.debug_avg = (self.debug_avg + diff) / 2
        
#        print('time debug diff: {} avg: {}'.format(diff, self.debug_avg))
        
    def now(self):
        return self.last + (time.time() - self.last_time)
