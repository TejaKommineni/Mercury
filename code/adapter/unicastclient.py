#!/usr/bin/env python

import udpiface

class ClientAddress:
    def __init__(self, cli_id, address, port):
        self.type = "UNICAST"
        self.cli_id = cli_id
        self.address = address
        self.port = port


__udpi = udpiface.UDPInterface()

def send_msg(caddr, msg):
    return __udpi.send_msg(caddr.address, caddr.port, msg)

def send_bcast(cliaddrs, msg):
    for caddr in cliaddrs:
        __udpi.send_msg(caddr.address, caddr.port, msg)
