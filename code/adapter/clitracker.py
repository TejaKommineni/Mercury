#!/usr/bin/env python

import os, sys
import uuid
import time
import random
import logging

sys.path.append(os.path.abspath("../common"))
import sessionmessage as sm
import mercury_pb2 as mproto
from scheduler import Scheduler

class ClientSession:
    def __init__(self, cli_id):
        self.cli_id = cli_id
        self.id = int(random.getrandbits(31))
        self.last_msg = time.time()
        self.msg_count = 0
        self.x_location = 0
        self.y_location = 0
        self.direction = 0
        self.speed = 0

    def update(self, msg):
        self.last_msg = time.time()
        self.msg_count += 1
        self.x_location = sm.get_msg_attr(msg, sm.CLIREP.X_LOC)
        self.y_location = sm.get_msg_attr(msg, sm.CLIREP.Y_LOC)
        self.direction = sm.get_msg_attr(msg, sm.CLIREP.DIRECTION)
        self.speed = sm.get_msg_attr(msg, sm.CLIREP.SPEED)
        
class AdapterClientTracker:
    CLIENT_TIMEOUT = 120
    CHECK_INTERVAL = 30

    def __init__(self, adapter):
        self.logger = logging.getLogger('Mercury.AdapterClientTracker')
        self.sessions = {}
        self.adapter = adapter
        self.check_interval = AdapterClientTracker.CHECK_INTERVAL
        self.client_timeout = AdapterClientTracker.CLIENT_TIMEOUT

    def configure(self, config):
        self.config = config['Adapter']
        if 'client_check_interval' in self.config:
            self.check_interval = int(self.config['client_check_interval'])
        if 'client_timeout' in self.config:
            self.client_timeout = int(self.config['client_timeout'])

    def start(self):
        # Start tracker GC.
        Scheduler().periodic(self.check_interval, self.check_clients)
        
    def check_clients(self, now):
        self.logger.debug("Checking for stale clients")
        for sess in self.sessions.values():
            if sess.last_msg + self.client_timeout < now:
                self.logger.debug("Deleting session for idle client: %d" % int(sess.cli_id))
                del self.sessions[sess.cli_id]

    def process_sess_mesg(self, msg):
        typesw = {
            mproto.SessionMsg.INIT:   self.cli_init,
            mproto.SessionMsg.CLOSE:  self.cli_close,
            mproto.SessionMsg.CLIREP: self.cli_report
        }
        def _bad(msg):
            self.logger.error("Unsupported session type: %s" %
                              msg.session_msg.type)
            return False
        handler = typesw.get(msg.session_msg.type, _bad)
        return handler(msg)

    def _mk_adapter_cli_sess_msg(self, cli_id, sess_id, msg_type):
        msg = mproto.MercuryMessage()
        msg.uuid = str(uuid.uuid4())
        msg.type = mproto.MercuryMessage.AD_SESS
        msg.src_addr.type = mproto.MercuryMessage.ADAPTER
        msg.dst_addr.type = mproto.MercuryMessage.CLIENT
        msg.dst_addr.cli_id = cli_id
        msg.session_msg.id = sess_id
        msg.session_msg.type = msg_type
        return msg
        
    def cli_init(self, msg):
        sess = None
        cli_id = msg.src_addr.cli_id
        self.logger.info("Session initiated for client %d" %
                         int(cli_id))
        if cli_id in self.sessions:
            # Client is reinitializing, but we still have state.
            sess = self.sessions[cli_id]
        else:
            sess = ClientSession(cli_id)
            self.sessions[cli_id] = sess
        sess.update(msg)
        retmsg = self._mk_adapter_cli_sess_msg(cli_id, sess.id,
                                               mproto.SessionMsg.INIT)
        sm.add_msg_attr(retmsg, sm.INIT.RESPONSE, sm.RV.SUCCESS)
        self.adapter.send_cli_msg(cli_id, retmsg)
        self.adapter.send_broker_cli_msg(cli_id, sess)

    def cli_close(self, msg):
        sess = None
        cli_id = msg.src_addr.cli_id
        if cli_id in self.sessions:
            sess = self.sessions[cli_id]
            sess.msg_count += 1
            self.logger.info("Closing session for client %d. Total messages: %d"
                % (int(cli_id), sess.msg_count))
            del self.sessions[msg.cli_id]
        else:
            self.logger.warning("Close received with no session. Client: %d" %
                                int(cli_id))

    def cli_report(self, msg):
        sess = None
        cli_id = msg.src_addr.cli_id
        if cli_id in self.sessions:
            # Log that we received a message.  Send along to broker.
            self.logger.debug("Received report from client %d" %
                              int(cli_id))
            sess = self.sessions[cli_id]
            sess.update(msg)
            self.adapter.send_broker_cli_msg(cli_id, sess)
        else:
            # Unknown client.  Send NACK.
            self.logger.warning("Received report from client without associated session, client: %d" %
                                int(cli_id))
            retmsg = self._mk_adapter_cli_sess_msg(cli_id, 0,
                                                   mproto.SessionMsg.CLOSE)
            sm.add_msg_attr(retmsg, sm.CLOSE.REASON, sm.RV.NOSESSION)
            self.adapter.send_cli_msg(cli_id, retmsg)
