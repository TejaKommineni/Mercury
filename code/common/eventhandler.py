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
            self.callback = None

        def fire(self, adevent):
            if self.callback:
                self.callback(adevent)
            else:
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
            rval = None
            self.evlock.acquire()
            if len(self.evlist):
                rval = self.evlist.pop(0)
            self.evlock.release()
            return rval

        def setcallback(self, cfunc):
            self.callback = cfunc

    instance = None

    def __init__(self):
        if not EventHandler.instance:
            EventHandler.instance = EventHandler.__EVHandler()

    def __getattr__(self, name):
        return getattr(self.instance, name)

