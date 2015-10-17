import time

DISABLE_MODULE = True


class Timer(object):
    def __init__(self, name=None, startnow=False):
        self.name = name
        self.start_time = None
        self.stop_time = None
        self.laps = []
        if startnow:
            self.start()

    def __repr__(self):
        return '<%sStart: %s, Stop: %s, Runtime: %s, Laps: %s>' % (
            self.name + ': ' if self.name else '',
            self.start_time,
            self.stop_time,
            self.runtime(),
            self.laps)

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.stop_time = time.time()

    def lap(self, name=None):
        self.laps.append((str(name), self.runtime()))

    def runtime(self):
        if self.stop_time:
            return self.stop_time - self.start_time
        else:
            return time.time() - self.start_time

    def getlap(self, lapnum):
        try:
            return self.laps[lapnum-1]
        except Exception:
            return None

    def reset(self):
        self.start_time = None
        self.stop_time = None
        self.laps = []
