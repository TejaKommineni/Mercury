#!/usr/bin/env python
 
import socket   #for sockets
import os, sys  #for exit
import uuid

sys.path.append(os.path.abspath("../common"))
import mercury_pb2
 
# create dgram udp socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    print 'Failed to create socket'
    sys.exit()


#host = 'localhost';
host = sys.argv[1];
port = 8888;
 
while(1) :
    msg = raw_input('Enter message to send : ')

    outmsg = mercury_pb2.MercuryMessage()
    outmsg.uuid = str(uuid.uuid4())
    outmsg.type = mercury_pb2.MercuryMessage.CLI_SESS
    outmsg.src_addr.type = mercury_pb2.MercuryMessage.CLIENT
    outmsg.src_addr.cli_id = 112233445566L
    outmsg.dst_addr.type = mercury_pb2.MercuryMessage.ADAPTER
    outmsg.session_msg.id = 9999
    outmsg.session_msg.type = mercury_pb2.SessionMsg.CLIREP
    newattr = outmsg.session_msg.attributes.add()
    newattr.key = "user_input"
    newattr.val = msg

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
