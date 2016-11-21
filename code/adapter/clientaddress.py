#!/usr/bin/env python

class CADDR_TYPES:
    UDP = 1

class UDPClientAddress:
    def __init__(self, cli_id, address, port):
        self.type = CADDR_TYPES.UDP
        self.cli_id = cli_id
        self.address = address
        self.port = port
        
