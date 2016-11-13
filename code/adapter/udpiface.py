#!/usr/bin/env python

import socket
import threading

RECVSIZE = 2**16 - 1

class AdapterUDPInterface:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.udprecv_thread = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.msglist = []
        self.msglock = threading.Lock()

    def configure(self, config):
        self.config   = config['Adapter']

    def bind(self):
        self.socket.bind(('', int(self.config['udp_port'])))
        print "UDP socket bound on port %s" % self.config['udp_port']
        self.udprecv_thread = threading.Thread(target=self.udp_recv)
        self.udprecv_thread.daemon = True
        self.udprecv_thread.start()

    def _add_msg(self, msg):
        self.msglock.acquire()
        self.msglist.append(msg)
        self.msglock.release()

    def udp_recv(self):
        while True:
            udpmsg = self.socket.recvfrom(RECVSIZE)
            print "Got UDP msg!"
            self._add_msg(udpmsg)

    def get_msg(self):
        msg = None
        self.msglock.acquire()
        if len(self.msglist):
            msg = self.msglist.pop()
        self.msglock.release()
        return msg

    def send_msg(self, host, port, msg):
        self.socket.sendto(msg, (host, port))
