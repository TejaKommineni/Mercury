#!/usr/bin/env python

import os, sys
import socket
import threading
import logging

sys.path.append(os.path.abspath("../common"))
import eventhandler

class UDPInterface:
    EVTYPE = "UDPReceiveEvent"
    RECVSIZE = 2**16 - 1

    class __UDPInterface:
        def __init__(self):
            self.logger = logging.getLogger('Mercury.UDPInterface')
            self.udprecv_thread = None
            self.evhandler = eventhandler.EventHandler()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.msglist = []
            self.msglock = threading.Lock()

        def configure(self, config):
            self.config   = config

        def bind(self):
            self.socket.bind(('', int(self.config['udp_port'])))
            self.logger.info("UDP socket bound on port %s" % self.config['service_port'])
            self.udprecv_thread = threading.Thread(target=self.udp_recv)
            self.udprecv_thread.daemon = True
            self.udprecv_thread.start()

        def _add_msg(self, msg):
            self.msglock.acquire()
            self.msglist.append(msg)
            self.msglock.release()

        def udp_recv(self):
            while True:
                udpmsg = self.socket.recvfrom(UDPInterface.RECVSIZE)
                self.logger.debug("Got UDP msg!")
                self._add_msg(udpmsg)
                ev = eventhandler.MercuryEvent(UDPInterface.EVTYPE)
                self.evhandler.fire(ev)

        def get_msg(self):
            msg = None
            self.msglock.acquire()
            if len(self.msglist):
                msg = self.msglist.pop(0)
            self.msglock.release()
            return msg

        def send_msg(self, host, port, msg):
            return self.socket.sendto(msg, (host, port))

    instance = None

    def __init__(self):
        if not UDPInterface.instance:
            UDPInterface.instance = UDPInterface.__UDPInterface()

    def __getattr__(self, name):
        return getattr(self.instance, name)
