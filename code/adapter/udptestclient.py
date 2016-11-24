#!/usr/bin/env python
 
import socket   #for sockets
import os, sys  #for exit
import uuid

sys.path.append(os.path.abspath("../common"))
import mercury_pb2
import sessionmessage as sm

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
    cli_id = sys.argv[2]
else:
    cli_id = 1234567890
    
port = 8888

def _add_sess_msg_attr(msg, key, val):
    attr = msg.session_msg.attributes.add()
    attr.key = key
    attr.val = str(val)

while(1) :
    msg = raw_input('Enter message to send : ')

    outmsg = mercury_pb2.MercuryMessage()
    outmsg.uuid = str(uuid.uuid4())
    outmsg.type = mercury_pb2.MercuryMessage.APP_CLI
    outmsg.src_addr.type = mercury_pb2.MercuryMessage.CLIENT
    outmsg.src_addr.cli_id = int(cli_id)
    outmsg.dst_addr.type = mercury_pb2.MercuryMessage.ADAPTER
    outmsg.session_msg.id = 0
    outmsg.session_msg.type = mercury_pb2.SessionMsg.CLIREP
    _add_sess_msg_attr(outmsg, sm.CLIREP.X_LOC, 1234)
    _add_sess_msg_attr(outmsg, sm.CLIREP.Y_LOC, 5467)
    _add_sess_msg_attr(outmsg, sm.CLIREP.DIRECTION, 360)
    _add_sess_msg_attr(outmsg, sm.CLIREP.SPEED, 60)

    try :
        #Set the whole string
        s.sendto(outmsg.SerializeToString(), (host, port))
         
        # receive data from client (data, addr)
        d = s.recvfrom(65535)
        reply = d[0]
        addr = d[1]

        inmsg = mercury_pb2.MercuryMessage()
        inmsg.ParseFromString(reply)
        print 'Server reply :\n%s' % inmsg
     
    except socket.error, msg:
        print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
