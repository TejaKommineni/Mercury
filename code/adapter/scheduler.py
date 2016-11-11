#!/usr/bin/env python

import logger
import time

MAXRELATIVE = 3600
TDELTA = 1

PERIODIC = 1
ONESHOT  = 2

#
# Mercury scheduler/timer utility module
#
class Scheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.schedule = []

    def configure(self, config):
        self.config = config['Scheduler']
        
    def periodic(self, interval, callback):
        if interval < 1:
            logger.error("Requested inverval too frequent: %d" % int(interval))
        self.schedule.append([PERIODIC, interval, time.time() + interval, callback])

    def oneshot(self, when, callback):
        if when < MAXRELATIVE:
            when = time.time() + when
        self.schedule.append([ONESHOT, when, callback])

    def check(self):
        now = time.time()
        for (task,details) in self.schedule:
            interval = when = callback = None
            if task[0] == PERIODIC:
                (interval, when, callback) = task[1:]
            elif task[0] == ONESHOT:
                (when, callback) = task[1:]
            if when <= now + TDELTA:
                callback()
                if interval:
                    task[2] = time.time() + interval
                else:
                    del self.schedule[task]
