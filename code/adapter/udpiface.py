#!/usr/bin/env python

import socket
import threading
import logging
import eventhandler

class AdapterUDPInterface:
    EVTYPE = "UDPReceiveEvent"
    RECVSIZE = 2**16 - 1

    def __init__(self):
        self.logger = logging.getLogger('Mercury.AdapterUDPInterface')
        self.udprecv_thread = None
        self.evhandler = eventhandler.AdapterEventHandler()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.msglist = []
        self.msglock = threading.Lock()

    def configure(self, config):
        self.config   = config['Adapter']

    def bind(self):
        self.socket.bind(('', int(self.config['udp_port'])))
        self.logger.info("UDP socket bound on port %s" % self.config['udp_port'])
        self.udprecv_thread = threading.Thread(target=self.udp_recv)
        self.udprecv_thread.daemon = True
        self.udprecv_thread.start()

    def _add_msg(self, msg):
        self.msglock.acquire()
        self.msglist.append(msg)
        self.msglock.release()

    def udp_recv(self):
        while True:
            udpmsg = self.socket.recvfrom(self.RECVSIZE)
            self.logger.debug("Got UDP msg!")
            self._add_msg(udpmsg)
            ev = eventhandler.AdapterEvent(AdapterUDPInterface.EVTYPE)
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
