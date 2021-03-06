#!/usr/bin/env python

import os, sys
import uuid
import time
import random
import logging
import copy
import threading

sys.path.append(os.path.abspath("../common"))
import sessionmessage as sm
import mercury_pb2 as mproto
import scheduler as sch

class ClientSession:
    def __init__(self, cli_id, dummy = False):
        self.cli_id = cli_id
        self.dummy = dummy
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

class ClientSessions:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

    def add(self, cli_id, sess):
        self.lock.acquire()
        self.sessions[cli_id] = sess
        self.lock.release()

    def delete(self, cli_id):
        self.lock.acquire()
        del self.sessions[cli_id]
        self.lock.release()

    def lookup(self, cli_id):
        sess = None
        self.lock.acquire()
        if cli_id in self.sessions:
            sess = self.sessions[cli_id]
        self.lock.release()
        return sess

    def update(self, cli_id, msg, dummy = False):
        sess = None
        self.lock.acquire()
        if not cli_id in self.sessions:
            sess = ClientSession(cli_id, dummy = dummy)
            self.sessions[cli_id] = sess
        else:
            sess = self.sessions[cli_id]
        sess.update(msg)
        self.lock.release()
        return sess

    def ticksession(self, cli_id):
        self.lock.acquire()
        if cli_id in self.sessions:
            sess = self.sessions[cli_id]
            sess.last_msg = time.time()
            sess.msg_count += 1
        self.lock.release()

    def getall(self):
        self.lock.acquire()
        rval = copy.deepcopy(self.sessions.values())
        self.lock.release()
        return rval
        
class AdapterClientTracker:
    CLIENT_TIMEOUT = 120
    HEARTBEAT_INTERVAL = 15
    CHECK_INTERVAL = 30

    def __init__(self, adapter):
        self.logger = logging.getLogger('Mercury.AdapterClientTracker')
        self.sessions = ClientSessions()
        self.adapter = adapter
        self.heartbeat_interval = AdapterClientTracker.HEARTBEAT_INTERVAL
        self.check_interval = AdapterClientTracker.CHECK_INTERVAL
        self.client_timeout = AdapterClientTracker.CLIENT_TIMEOUT

    def configure(self, config):
        self.config = config['Adapter']
        if 'client_check_interval' in self.config:
            self.check_interval = int(self.config['client_check_interval'])
        if 'heartbeat_interval' in self.config:
            self.heartbeat_interval = int(self.config['heartbeat_interval'])
        if 'client_timeout' in self.config:
            self.client_timeout = int(self.config['client_timeout'])

    def start(self):
        sched = sch.Scheduler()
        # Start heartbeat sender.
        sched.periodic(self.heartbeat_interval, self.send_heartbeat)
        # Start tracker GC.
        sched.periodic(self.check_interval, self.check_clients)
        
    def check_clients(self, now):
        self.logger.debug("Checking for stale clients")
        for sess in self.sessions.getall():
            if sess.last_msg + self.client_timeout < now:
                self.logger.debug("Deleting session for idle client: %d" % int(sess.cli_id))
                self.adapter.cliaddrs.delete(sess.cli_id)
                self.sessions.delete(sess.cli_id)

    def send_heartbeat(self, now):
        self.logger.debug("Sending heartbeat to clients")
        bcast = self._mk_adapter_cli_sess_msg(0, 0, mproto.SessionMsg.HB)
        self.adapter.send_cli_bcast(bcast.SerializeToString())

    def check_session(self, msg):
        cli_id = msg.src_addr.cli_id
        if not self.sessions.lookup(cli_id):
            self.send_cli_error(cli_id)
            return False
        else:
            self.sessions.ticksession(cli_id)
            return True
                
    def process_sess_mesg(self, msg, dummy = 0):
        typesw = {
            mproto.SessionMsg.INIT:   self.cli_init,
            mproto.SessionMsg.CLOSE:  self.cli_close,
            mproto.SessionMsg.CLIREP: self.cli_report,
            mproto.SessionMsg.ECHO:   self.cli_echo
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
        cli_id = msg.src_addr.cli_id
        self.logger.info("Session initiated for client %d" %
                         int(cli_id))
        sess = self.sessions.update(cli_id, msg)
        retmsg = self._mk_adapter_cli_sess_msg(cli_id, sess.id,
                                               mproto.SessionMsg.INIT)
        sm.add_msg_attr(retmsg, sm.INIT.RESPONSE, sm.RV.SUCCESS)
        self.adapter.send_cli_msg(cli_id, retmsg.SerializeToString())
        self.adapter.send_broker_cli_report(cli_id, sess)

    def cli_close(self, msg):
        cli_id = msg.src_addr.cli_id
        sess = self.sessions.lookup(sess)
        if sess:
            sess.msg_count += 1
            self.logger.info("Closing session for client %d. Total messages: %d"
                % (int(cli_id), sess.msg_count))
            self.sessions.delete(cli_id)
        else:
            self.logger.warning("Close received with no session. Client: %d" %
                                int(cli_id))

    def cli_report(self, msg):
        cli_id = msg.src_addr.cli_id
        if self.sessions.lookup(cli_id):
            # Log that we received a message.  Send along to broker.
            self.logger.debug("Received report from client %d" %
                              int(cli_id))
            sess = self.sessions.update(cli_id, msg)
            self.adapter.send_broker_cli_report(cli_id, sess)
        elif msg.type == mproto.MercuryMessage.APP_CLI:
            # Dummy passthru session for simulations.
            self.logger.debug("Creating session for dummy client: %d" %
                              int(cli_id))
            sess = self.sessions.update(cli_id, dummy = True)
            self.adapter.send_broker_cli_report(cli_id, sess)
        else:
            self.send_cli_error(cli_id)

    def cli_echo(self, msg):
        cli_id = msg.src_addr.cli_id
        if self.sessions.lookup(cli_id):
            # Log that we received an echo message. Return reply.
            self.logger.debug("Received echo request from client %d" %
                              int(cli_id))
            msg.type = mproto.MercuryMessage.AD_SESS
            msg.src_addr.type = mproto.MercuryMessage.ADAPTER
            msg.dst_addr.type = mproto.MercuryMessage.CLIENT
            msg.dst_addr.cli_id = cli_id
            self.adapter.send_cli_msg(cli_id, msg.SerializeToString())
        else:
            self.send_cli_error(cli_id)

    def send_cli_error(self, cli_id):
        self.logger.warning("Received message from client without associated session, client: %d" % int(cli_id))
        retmsg = self._mk_adapter_cli_sess_msg(cli_id, 0,
                                               mproto.SessionMsg.CLOSE)
        sm.add_msg_attr(retmsg, sm.CLOSE.REASON, sm.RV.NOSESSION)
        self.adapter.send_cli_msg(cli_id, retmsg.SerializeToString())

    def get_clients_in_aoi(self, aoi):
        clist = []
        for sess in self.sessions.getall():
            if aoi.in_aoi(sess.x_location, sess.y_location):
                clist.append(sess.cli_id)
        return clist
