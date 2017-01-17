#!/usr/bin/env python

import os, sys
import time
import socket
import array
import threading
import uuid

sys.path.append(os.path.abspath("../common"))
import mercury_pb2
import pubsubmessage as psm
import appclimessage as acm

# create dgram udp socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print 'Failed to create socket'
    sys.exit()


#host = 'localhost';
if len(sys.argv) < 2:
    print "Usage: echotester.py <dest> <count> <rate>"
    sys.exit(1)

host = "127.0.0.1"
port = 9999
app_id = 333666999

fuuid = str(uuid.uuid4())

timings = array.array('f')
tsattr = None

dest = sys.argv[1]
count = int(sys.argv[2])
rate = float(sys.argv[3])
pgap = 1/rate

def _add_pubsub_msg_attr(msg, key, val):
    attr = msg.pubsub_msg.attributes.add()
    attr.key = key
    attr.val = str(val)
    return attr

def _add_appcli_msg_attr(msg, key, val):
    attr = msg.appcli_msg.attributes.add()
    attr.key = key
    attr.val = str(val)
    return attr

def _mk_broker_echo_msg():
    global tsattr
    msg = mercury_pb2.MercuryMessage()
    msg.uuid = fuuid
    msg.type = mercury_pb2.MercuryMessage.CLI_PUB
    msg.src_addr.type = mercury_pb2.MercuryMessage.APP
    msg.src_addr.app_id = int(app_id)
    msg.dst_addr.type = mercury_pb2.MercuryMessage.CLIENT
    msg.pubsub_msg.topic = psm.UTILITY.TYPES.ECHO
    _add_pubsub_msg_attr(msg, psm.UTILITY.ATTRIBUTES.APP_ID, app_id)
    tsattr = _add_pubsub_msg_attr(msg, psm.UTILITY.ATTRIBUTES.ECHO_STAMP, 0)
    return msg

def _mk_client_echo_msg():
    global tsattr
    msg = mercury_pb2.MercuryMessage()
    msg.uuid = fuuid
    msg.type = mercury_pb2.MercuryMessage.APP_CLI
    msg.src_addr.type = mercury_pb2.MercuryMessage.APP
    msg.src_addr.app_id = int(app_id)
    msg.dst_addr.type = mercury_pb2.MercuryMessage.CLIENT
    msg.appcli_msg.type = psm.UTILITY.TYPES.ECHO
    _add_appcli_msg_attr(msg, psm.UTILITY.ATTRIBUTES.APP_ID, app_id)
    tsattr = _add_appcli_msg_attr(msg, psm.UTILITY.ATTRIBUTES.ECHO_STAMP, 0)
    return msg

def _mk_adapter_echo_msg():
    global tsattr
    msg = mercury_pb2.MercuryMessage()
    msg.uuid = fuuid
    msg.type = mercury_pb2.MercuryMessage.APP_CLI
    msg.src_addr.type = mercury_pb2.MercuryMessage.APP
    msg.src_addr.app_id = int(app_id)
    msg.dst_addr.type = mercury_pb2.MercuryMessage.CLIENT
    msg.appcli_msg.type = psm.UTILITY.TYPES.ECHO_ADAPTER
    _add_appcli_msg_attr(msg, psm.UTILITY.ATTRIBUTES.APP_ID, app_id)
    tsattr = _add_appcli_msg_attr(msg, psm.UTILITY.ATTRIBUTES.ECHO_STAMP, 0)
    return msg

def _update_echo_tstamp(val):
    tsattr.val = repr(val)

def process_incoming():
    inmsg = mercury_pb2.MercuryMessage()
    while True:
        # receive data from client (data, addr)
        udpmsg = s.recvfrom(65535)
        now = time.time()
        inmsg.ParseFromString(udpmsg[0])
        tdiff = None
        if inmsg.type == mercury_pb2.MercuryMessage.PUB_CLI:
            tdiff = now - float(psm.get_msg_attr(inmsg, psm.UTILITY.ATTRIBUTES.ECHO_STAMP))
        elif inmsg.type == mercury_pb2.MercuryMessage.CLI_APP:
            pstamp = float(acm.get_msg_attr(inmsg, psm.UTILITY.ATTRIBUTES.ECHO_STAMP))
            tdiff = now - pstamp
        else:
            print "Unknown message type!"
        timings.append(tdiff)

inthr = threading.Thread(target=process_incoming)
inthr.daemon = True
inthr.start()

outmsg = None
if dest == "broker":
    outmsg = _mk_broker_echo_msg()
elif dest == "client":
    outmsg = _mk_client_echo_msg()
elif dest == "adapter":
    outmsg = _mk_adapter_echo_msg()
else:
    print "Unknown destination: %s" % dest
    sys.exit(1)

while count > 0:
    _update_echo_tstamp(time.time())
    s.sendto(outmsg.SerializeToString(), (host, port))
    time.sleep(pgap)
    count -= 1

print "Waiting a bit for final echo replies to arrive."
time.sleep(5)

for tm in timings:
    print tm
