#!/usr/bin/env python

import logging
import time
import sortedcontainers

MAXRELATIVE = 3600

PERIODIC = 1
ONESHOT  = 2

#
# Mercury scheduler/timer utility module
#
class Scheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.schedule = sortedcontainers.SortedListWithKey(key = lambda x: x['when'])

    def configure(self, config):
        self.config = config['Scheduler']
        
    def periodic(self, interval, callback):
        if interval < 1:
            self.logger.error("Requested inverval too frequent: %d" % int(interval))
        when = int(time.time()) + interval
        self.schedule.add({ 'when'     : when,
                            'type'     : PERIODIC,
                            'interval' : interval,
                            'callback' : callback })

    def oneshot(self, when, callback):
        now = int(time.time())
        if when < 1:
            self.logger.error("Requested time is too soon: %d" % when)
        if when < now:
            if when > MAXRELATIVE:
                self.logger.error("Relative oneshot offset too long: %d" % when)
            when = now + when
        self.schedule.add({ 'when'     : when,
                            'type'     : ONESHOT,
                            'callback' : callback })

    def check(self):
        now = int(time.time())
        for ival in self.schedule.irange({'when' : 0}, {'when' : now}):
            self.schedule.remove(ival)
            ival['callback'](now)
            if ival['type'] == PERIODIC:
                ival['when'] = now + ival['interval']
                self.schedule.add(ival)
