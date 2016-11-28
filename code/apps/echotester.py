#!/usr/bin/env python

import os, sys
import time
import socket
import threading
import uuid

sys.path.append(os.path.abspath("../common"))
import mercury_pb2
import pubsubmessage as psm

# create dgram udp socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print 'Failed to create socket'
    sys.exit()


#host = 'localhost';
if len(sys.argv) < 2:
    print "Usage: echotester.py <count> <rate>"
    sys.exit()

host = "127.0.0.1"
port = 9999
app_id = 333666999

count = int(sys.argv[1])
rate = float(sys.argv[2])
pgap = 1/rate

def _add_pubsub_msg_attr(msg, key, val):
    attr = msg.pubsub_msg.attributes.add()
    attr.key = key
    attr.val = str(val)

def _mk_echo_msg(eid):
    msg = mercury_pb2.MercuryMessage()
    msg.uuid = str(uuid.uuid4())
    msg.type = mercury_pb2.MercuryMessage.CLI_PUB
    msg.src_addr.type = mercury_pb2.MercuryMessage.APP
    msg.src_addr.app_id = int(app_id)
    msg.dst_addr.type = mercury_pb2.MercuryMessage.CLIENT
    msg.pubsub_msg.topic = psm.UTILITY.TYPES.ECHO
    _add_pubsub_msg_attr(msg, psm.UTILITY.ATTRIBUTES.APP_ID, str(app_id))
    _add_pubsub_msg_attr(msg, psm.UTILITY.ATTRIBUTES.ECHO_STAMP, str(eid))
    return msg

def process_incoming():
    while True:
        # receive data from client (data, addr)
        udpmsg = s.recvfrom(65535)
        now = time.time()
        inmsg = mercury_pb2.MercuryMessage()
        inmsg.ParseFromString(udpmsg[0])
        print "Message RTT: %f" % \
            (now - float(psm.get_msg_attr(inmsg, psm.UTILITY.ATTRIBUTES.ECHO_STAMP)))

inthr = threading.Thread(target=process_incoming)
inthr.daemon = True
inthr.start()


while count > 0:
    outmsg = _mk_echo_msg(time.time())
    s.sendto(outmsg.SerializeToString(), (host, port))
    time.sleep(pgap)
    count -= 1

time.sleep(5)
