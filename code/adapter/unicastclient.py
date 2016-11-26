#!/usr/bin/env python

import os, sys

sys.path.append(os.path.abspath("../common"))
import udpiface

class ClientAddress:
    def __init__(self, cli_id, address, port, dummy = False):
        self.type = "UNICAST"
        self.dummy = dummy
        self.cli_id = cli_id
        self.address = address
        self.port = port


__udpi = udpiface.UDPInterface()

def send_msg(caddr, msg):
    return __udpi.send_msg(caddr.address, caddr.port, msg)

def send_bcast(cliaddrs, msg):
    for caddr in cliaddrs:
        if caddr.dummy: continue
        __udpi.send_msg(caddr.address, caddr.port, msg)
