#!/usr/bin/env python

import os, sys
import logging
import time
import uuid

sys.path.append(os.path.abspath("../common"))
import mercury_pb2 as mproto
import sessionmessage as sm
import areaofinterest as aoi
import scheduler as sch

class ClientSession:
    DEFAULT_REPORT_INTERVAL = 15
    HEARTBEAT_TIMEOUT = 120
    BACKOFF_DIVISOR = 1.1
    MIN_INIT_WAIT = 1
    MAX_INIT_WAIT = 10

    def __init__(self, client):
        self.logger = logging.getLogger("Mercury.ClientSession")
        self.client = client
        self.sched = sch.Scheduler()
        self.repint = ClientSession.DEFAULT_REPORT_INTERVAL
        self.session_active = False
        self.last_hb = 0
        self.cur_wait = 0
        self.x_location = 0
        self.y_location = 0
        self.direction = 0
        self.speed = 0

    def configure(self, config):
        self.config = config
        self.repint = int(config['report_interval'])

    def process_adapter_msg(self, msg):
        smsg = msg.session_msg
        now = time.time()
        if smsg.type == mproto.SessionMsg.INIT:
            res = sm.get_msg_attr(msg, sm.INIT.RESPONSE)
            if res == sm.RV.SUCCESS:
                self.logger.info("Connected to adapter!")
                self.session_active = True
                self.last_hb = now
        elif smsg.type == mproto.SessionMsg.HB:
            self.logger.debug("Received heartbeat from adapter")
            self.last_hb = now

    def _mk_init_msg(self):
        msg = mproto.MercuryMessage()
        msg.uuid = str(uuid.uuid4())
        msg.type = mproto.MercuryMessage.CLI_SESS
        msg.src_addr.type = mproto.MercuryMessage.CLIENT
        msg.src_addr.cli_id = int(self.client.cli_id)
        msg.dst_addr.type = mproto.MercuryMessage.ADAPTER
        msg.session_msg.type = mproto.SessionMsg.INIT
        sm.add_msg_attr(msg, sm.CLIREP.X_LOC, self.x_location)
        sm.add_msg_attr(msg, sm.CLIREP.Y_LOC, self.y_location)
        sm.add_msg_attr(msg, sm.CLIREP.DIRECTION, self.direction)
        sm.add_msg_attr(msg, sm.CLIREP.SPEED, self.speed)
        return msg

    def _mk_report_msg(self):
        msg = self._mk_init_msg()
        msg.session_msg.type = mproto.SessionMsg.CLIREP
        return msg

    def initialize(self):
        self.session_active = False
        initmsg = self._mk_init_msg()
        self.client.send_adapter_message(initmsg.SerializeToString())
        self.curwait = ClientSession.MIN_INIT_WAIT
        self.sched.oneshot(self.curwait, self.check_session, 1)

    def send_client_report(self, now):
        # FIXME: heartbeat timeout should be a function of reporting interval
        #        and/or configurable.
        if self.last_hb + ClientSession.HEARTBEAT_TIMEOUT < now:
            self.logger.warning("Adapter heartbeats missed! Reinitializing session.")
            self.initialize()
            return
        elif self.session_active:
            self.logger.debug("Sending client report.")
            repmsg = self._mk_report_msg()
            self.client.send_adapter_message(repmsg.SerializeToString())
            self.sched.oneshot(self.repint, self.send_client_report)

    def check_session(self, now):
        if not self.session_active:
            bodiv = ClientSession.BACKOFF_DIVISOR
            maxwait = ClientSession.MAX_INIT_WAIT
            initmsg = self._mk_init_msg()
            self.client.send_adapter_message(initmsg.SerializeToString())
            self.curwait = (self.curwait * bodiv)
            if self.curwait > maxwait: self.curwait = maxwait
            self.sched.oneshot(self.curwait, self.check_session)
        else:
            self.sched.oneshot(self.repint, self.send_client_report, 1)
