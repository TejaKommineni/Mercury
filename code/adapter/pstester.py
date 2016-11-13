#!/usr/bin/env python

import sys, time
import json
import configparser
import psubiface
import scheduler

CONFFILE = "config.ini"

def main(*args):
    config = configparser.ConfigParser()
    config.read(CONFFILE)
    sched = scheduler.Scheduler()
    psub = psubiface.AdapterPubSubInterface(sched)
    psub.configure(config)
    psub.connect()

    msg1 = {'foo':1, 'bar':2, 'baz':3}
    psub.send_msg('Moving_Objects', json.dumps(msg1))

    msg2 = {'x_location':100, 'y_location':200}
    psub.send_msg('Emergency', json.dumps(msg2))

    for i in range(11):
        colmsg = {'x_location':35, 'y_location':35}
        psub.send_msg('Collision', json.dumps(colmsg))
    
    while True:
        msg = psub.get_msg()
        if msg: print "Got message: %s" % msg.value
        time.sleep(1)

if __name__ == "__main__":
    main(sys.argv)
