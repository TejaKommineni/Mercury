#!/usr/bin/env python

import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

while(1):
    msg = raw_input('Enter message to send : ')
    if not msg:
	sys.exit()

    try:
        #Set the whole string
	sock.sendto(msg, ("239.192.0.100", 8888))

    except socket.error, msg:
        print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
