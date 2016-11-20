#!/usr/bin/env python

import sys
import time
import random
import string
import threading
import eventhandler

NUMTHREADS = 20

def genfunc():
    evhandler = eventhandler.AdapterEventHandler()
    thrid = str(threading.current_thread().ident)
    evid = 0

    while True:
        evid += 1
        evtype = 'Thread-' + thrid + '-TestEvent-' + str(evid)
        evdata = []
        for idx in range(random.randint(1,8)):
            evdata.append(''.join(random.choice(string.ascii_uppercase) for _ in range(12)))
        ev = eventhandler.AdapterEvent(evtype, evdata)
        evhandler.fire(ev)
        time.sleep(random.uniform(0.1*NUMTHREADS/2, NUMTHREADS/4))

def main(*argv):
    evhandler = eventhandler.AdapterEventHandler()

    thrlist = []
    for i in range(NUMTHREADS):
        thr = threading.Thread(target=genfunc)
        thr.daemon = True
        thr.start()
        thrlist.append(thr)

    while True:
        evhandler.wait()
        while evhandler.hasevents():
            adev = evhandler.pop()
            print "%s: %s" % (adev.evtype, adev.evdata)

if __name__ == "__main__":
    main(sys.argv)
