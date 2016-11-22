#!/usr/bin/env python

import threading

class MercuryEvent:
    def __init__(self, evtype, evdata = None):
        self.evtype = evtype
        self.evdata = evdata

class EventHandler:
    class __EVHandler:
        def __init__(self):
            self.evlock = threading.Lock()
            self.ev = threading.Event()
            self.evlist = []

        def fire(self, adevent):
            self.evlock.acquire()
            self.evlist.append(adevent)
            self.evlock.release()
            self.ev.set()

        def wait(self, timeout = None):
            rv = self.ev.wait(timeout)
            self.ev.clear()
            return rv

        def hasevents(self):
            self.evlock.acquire()
            rval = len(self.evlist)
            self.evlock.release()
            return rval

        def pop(self):
            self.evlock.acquire()
            rval = self.evlist.pop(0)
            self.evlock.release()
            return rval

    instance = None

    def __init__(self):
        if not EventHandler.instance:
            EventHandler.instance = EventHandler.__EVHandler()

    def __getattr__(self, name):
        return getattr(self.instance, name)

