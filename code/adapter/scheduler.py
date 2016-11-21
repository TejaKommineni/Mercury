#!/usr/bin/env python

import logging
import time
import threading
import sortedcontainers

from eventhandler import *

#
# Mercury scheduler/timer utility module (singleton scheduler).
#
class Scheduler:
    EVTYPE = "SchedulerEvent"
    MAXRELATIVE = 3600
    MINCHECK = 5
    PERIODIC = 1
    ONESHOT  = 2

    class __Sched:
        def __init__(self):
            self.logger = logging.getLogger("Mercury.Scheduler")
            self.timer_thread = None
            self.evhandler = AdapterEventHandler()
            self.schedule = sortedcontainers.SortedListWithKey(key = lambda x: x['when'])

        def configure(self, config):
            self.config = config

        def periodic(self, interval, callback):
            now = int(time.time())
            interval = int(interval)
            if interval < Scheduler.MINCHECK:
                self.logger.error("Requested inverval too frequent: %d" % int(interval))
                raise
            when = now + interval
            self.logger.debug("Periodic job: Interval: %d. Function: %s" %
                              (interval, callback))
            self.schedule.add({ 'when'     : when,
                                'type'     : Scheduler.PERIODIC,
                                'interval' : interval,
                                'callback' : callback })
            self._setup_check_timer(now)

        def oneshot(self, when, callback):
            now = int(time.time())
            when = int(when)
            if when < Scheduler.MINCHECK:
                self.logger.error("Requested time is too soon: %d" % when)
                raise
            if when < now:
                if when > Scheduler.MAXRELATIVE:
                    self.logger.error("Relative oneshot offset too long: %d" % when)
                when = now + when
            self.schedule.add({ 'when'     : when,
                                'type'     : Scheduler.ONESHOT,
                                'callback' : callback })
            self._setup_check_timer(now)

        def check(self):
            self.logger.debug("Scheduler check fired!")
            now = int(time.time())
            for ival in self.schedule.irange({'when' : 0}, {'when' : now}):
                self.schedule.remove(ival)
                ival['callback'](now)
                if ival['type'] == Scheduler.PERIODIC:
                    ival['when'] = now + ival['interval']
                    self.schedule.add(ival)
            self._setup_check_timer(now)

        def _fire(self):
            ev = AdapterEvent(Scheduler.EVTYPE)
            self.evhandler.fire(ev)

        def _setup_check_timer(self, now = int(time.time())):
            if not len(self.schedule): return
            if self.timer_thread:
                self.timer_thread.cancel()
                self.timer_thread = None
            nextdl = self.schedule[0]['when'] - now
            if nextdl < Scheduler.MINCHECK:
                nextdl = Scheduler.MINCHECK
            self.timer_thread = threading.Timer(nextdl, self._fire)
            self.timer_thread.setDaemon(True)
            self.timer_thread.start()

        def stop(self):
            self.timer_thread.cancel()

    instance = None

    def __init__(self):
        if not Scheduler.instance:
            Scheduler.instance = Scheduler.__Sched()

    def __getattr__(self, name):
        return getattr(self.instance, name)
