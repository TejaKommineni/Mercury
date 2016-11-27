#!/usr/bin/env python
 
import socket   #for sockets
import os, sys  #for exit
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
if len(sys.argv) > 1:
    host = sys.argv[1]
else:
    host = "localhost"

if len(sys.argv) > 2:
    app_id = sys.argv[2]
else:
    app_id = 8675309
    
port = 9999

def _add_pubsub_msg_attr(msg, key, val):
    attr = msg.pubsub_msg.attributes.add()
    attr.key = key
    attr.val = str(val)

def _mk_safety_msg(topic):
    msg = mercury_pb2.MercuryMessage()
    msg.uuid = str(uuid.uuid4())
    msg.type = mercury_pb2.MercuryMessage.CLI_PUB
    msg.src_addr.type = mercury_pb2.MercuryMessage.APP
    msg.src_addr.app_id = int(app_id)
    msg.dst_addr.type = mercury_pb2.MercuryMessage.CLIENT
    msg.pubsub_msg.topic = topic
    _add_pubsub_msg_attr(msg, psm.SAFETY.ATTRIBUTES.X_LOC, 1)
    _add_pubsub_msg_attr(msg, psm.SAFETY.ATTRIBUTES.Y_LOC, 1)
    _add_pubsub_msg_attr(msg, psm.SAFETY.ATTRIBUTES.RADIUS, 5)
    return msg

def _mk_subscr_msg(topic):
    msg = mercury_pb2.MercuryMessage()
    msg.uuid = str(uuid.uuid4())
    msg.type = mercury_pb2.MercuryMessage.CLI_SUBSCR
    msg.src_addr.type = mercury_pb2.MercuryMessage.APP
    msg.src_addr.app_id = int(app_id)
    msg.dst_addr.type = mercury_pb2.MercuryMessage.PUBSUB
    msg.pubsub_msg.topic = topic
    return msg

def process_incoming():
    while True:
        # receive data from client (data, addr)
        d = s.recvfrom(65535)
        reply = d[0]
        addr = d[1]
        
        inmsg = mercury_pb2.MercuryMessage()
        inmsg.ParseFromString(reply)
        print 'Message received:\n%s' % inmsg

inthr = threading.Thread(target=process_incoming)
inthr.daemon = True
inthr.start()

subscr = _mk_subscr_msg(psm.SAFETY.TYPES.ALL)
s.sendto(subscr.SerializeToString(), (host, port))

while True:
    topic = raw_input('Enter safety message type to send: ')
    if not topic:
        print "Topic list: %s" % psm.SAFETY.TYPELIST
        continue
    if topic not in psm.SAFETY.TYPELIST:
        print "Unknown type: %s" % topic
        continue
    outmsg = _mk_safety_msg(topic)    
    s.sendto(outmsg.SerializeToString(), (host, port))
