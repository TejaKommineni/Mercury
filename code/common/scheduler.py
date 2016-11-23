#!/usr/bin/env python

import os, sys
import logging
import random
import time
import threading
import sortedcontainers

sys.path.append(os.path.abspath("../common"))
import eventhandler

#
# Mercury scheduler/timer utility module (singleton scheduler).
#
class Scheduler:
    EVTYPE = "SchedulerEvent"
    MAXRELATIVE = 3600
    MINCHECK = 1
    PERIODIC = 1
    ONESHOT  = 2

    class __Sched:
        def __init__(self):
            self.logger = logging.getLogger("Mercury.Scheduler")
            self.timer_thread = None
            self.evhandler = eventhandler.EventHandler()
            self.schedule = sortedcontainers.SortedListWithKey(key = lambda x: x['when'])

        def configure(self, config):
            self.config = config

        def periodic(self, interval, callback, randoffset = 0):
            now = time.time()
            interval = float(interval)
            if interval < Scheduler.MINCHECK:
                self.logger.error("Requested inverval too frequent: %f" % interval)
                raise RuntimeError, "Stopping!"
            when = now + interval
            if randoffset:
                when = when + random.uniform(0, randoffset)
            self.logger.debug("Periodic job: Interval: %d. Function: %s" %
                              (interval, callback))
            self.schedule.add({ 'when'     : when,
                                'type'     : Scheduler.PERIODIC,
                                'interval' : interval,
                                'callback' : callback })
            self._setup_check_timer(now)

        def oneshot(self, when, callback, randoffset = 0):
            now = time.time()
            when = float(when)
            if randoffset:
                when = when + random.uniform(0, randoffset)
            if when < Scheduler.MINCHECK:
                self.logger.error("Requested time is too soon: %f" % when)
                raise RuntimeError, "Stopping!"
            if when < now:
                if when > Scheduler.MAXRELATIVE:
                    self.logger.error("Relative oneshot offset too long: %f" % when)
                when = now + when
            self.schedule.add({ 'when'     : when,
                                'type'     : Scheduler.ONESHOT,
                                'callback' : callback })
            self._setup_check_timer(now)

        def check(self):
            self.logger.debug("Scheduler check fired!")
            now = time.time()
            for ival in self.schedule.irange({'when' : 0}, {'when' : now}):
                self.schedule.remove(ival)
                ival['callback'](now)
                if ival['type'] == Scheduler.PERIODIC:
                    ival['when'] = now + ival['interval']
                    self.schedule.add(ival)
            self._setup_check_timer(now)

        def _fire(self):
            ev = eventhandler.MercuryEvent(Scheduler.EVTYPE)
            self.evhandler.fire(ev)

        def _setup_check_timer(self, now = time.time()):
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
