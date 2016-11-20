#!/usr/bin/env python

import os, sys
import time
import random

sys.path.append(os.path.abspath("../common"))
import sessionmessage as sm
from scheduler import Scheduler

class ClientSession:
    def __init__(self, cli_id):
        self.cli_id = cli_id
        self.id = int(random.getrandbits(32))
        self.last_msg = time.time()
        self.msg_count = 1
        self.x_loc = 0
        self.y_loc = 1

class AdapterClientTracker:
    MAX_CLI_INTERVAL = 120
    CHECKINTERVAL = 30

    def __init__(self, adapter):
        self.sessions = {}
        self.adapter = adapter

    def configure(self, config):
        self.config = config['Adapter']
        # Start tracker GC.
        Scheduler().periodic(self.CHECKINTERVAL, self.check_clients)

    def check_clients(self, now):
        print "Checking for stale clients"
        for sess in self.sessions.values():
            if sess.last_msg + self.MAX_CLI_INTERVAL < now:
                print "Deleting session for idle client: %d" % int(sess.cli_id)
                del self.sessions[sess.cli_id]

    def process_sess_mesg(self, msg):
        typesw = {
            sm.TYPE.INIT:   self.cli_init,
            sm.TYPE.CLOSE:  self.cli_close,
            sm.TYPE.CLIREP: self.cli_report
        }
        def _bad(msg):
            raise RuntimeError, "Unsupported session type: %s" % msg.type
        handler = typesw.get(msg.type, _bad)
        return handler(msg)

    def cli_init(self, msg):
        sess = None
        if msg.cli_id in self.sessions:
            # Client is reinitializing, but we still have state.
            sess = self.sessions[msg.cli_id]
        else:
            sess = ClientSession(msg.cli_id)
            sess.x_loc = msg.getval(sm.CLIREP.X_LOC)
            sess.y_loc = msg.getval(sm.CLIREP.Y_LOC)
            sess.direc = msg.getval(sm.CLIREP.DIRECTION)
            sess.speed = msg.getval(sm.CLIREP.SPEED)
            self.sessions[msg.cli_id] = sess
        retmsg = sm.SessionMessage(sm.TYPE.INIT)
        retmsg.id = sess.id
        retmsg.add_kv(sm.INIT.RESPONSE, sm.RV.SUCCESS)
        self.adapter.send_cli_msg(retmsg)

    def cli_close(self, msg):
        sess = None
        if msg.cli_id in self.sessions:
            sess = self.sessions[msg.cli_id]
            sess.msg_count += 1
            print "Closing session for client: %d Total messages: %d" \
                % (int(msg.cli_id), sess.msg_count)
            del self.sessions[msg.cli_id]
        else:
            print "Close received for unknown cient: %d" % int(msg.cli_id)

    def cli_report(self, msg):
        sess = None
        if msg.cli_id in self.sessions:
            # Log that we received a message.  Send along to broker.
            sess = self.sessions[msg.cli_id]
            sess.msg_count += 1
            sess.last_msg = time.time()
            sess.x_loc = msg.getval(sm.CLIREP.X_LOC)
            sess.y_loc = msg.getval(sm.CLIREP.Y_LOC)
            sess.direc = msg.getval(sm.CLIREP.DIRECTION)
            sess.speed = msg.getval(sm.CLIREP.SPEED)
            self.adapter.send_broker_msg(msg)
        else:
            # Unknown client.  Send NACK.
            retmsg = sm.SessionMessage(sm.TYPE.CLOSE)
            retmsg.id = sess.id
            retmsg.add_kv(sm.CLOSE.REASON, sm.RV.NACK)
            self.adapter.send_cli_msg(retmsg)
