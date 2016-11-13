#!/usr/bin/env python

import os, sys, time
import json
import uuid
import configparser
import udpiface
import scheduler

sys.path.append(os.path.abspath("../common"))
import mercury_pb2

CONFFILE = "config.ini"

def main(*args):
    config = configparser.ConfigParser()
    config.read(CONFFILE)
    sched = scheduler.Scheduler()
    udpi = udpiface.AdapterUDPInterface(sched)
    udpi.configure(config)
    udpi.bind()

    while True:
        udpmsg = udpi.get_msg()
        if udpmsg:
            cli_msg  = udpmsg[0]
            cli_addr = udpmsg[1]
            print "Received message from [%s:%d]" % (cli_addr[0], cli_addr[1])
            inmsg = mercury_pb2.MercuryMessage()
            inmsg.ParseFromString(cli_msg)
            #if hasattr(inmsg, "session_msg"):
            #    for attr in inmsg.session_msg.attributes:
            #        print "%s: %s" % (attr.key, attr.val)
            print inmsg
            outmsg = mercury_pb2.MercuryMessage()
            outmsg.uuid = str(uuid.uuid4())
            outmsg.type = mercury_pb2.MercuryMessage.AD_SESS
            outmsg.src_addr.type = mercury_pb2.MercuryMessage.ADAPTER
            outmsg.dst_addr.type = inmsg.src_addr.type
            outmsg.dst_addr.cli_id = inmsg.src_addr.cli_id
            outmsg.session_msg.id = inmsg.session_msg.id
            outmsg.session_msg.type = mercury_pb2.SessionMsg.HB
            newattr = outmsg.session_msg.attributes.add()
            newattr.key = "response"
            newattr.val = "This is your response..."
            udpi.send_msg(cli_addr[0], cli_addr[1], outmsg.SerializeToString())
        time.sleep(1)

if __name__ == "__main__":
    main(sys.argv)
