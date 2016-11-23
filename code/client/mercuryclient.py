#!/usr/bin/env python
import os, sys
import string
import time
import logging
import socket
import json

import configparser

sys.path.append(os.path.abspath("../common"))
import udpiface
import eventhandler
import session
import mercury_pb2 as mproto
import sessionmessage as sm
import areaofinterest as aoi
import pubsubmessage as psm
import scheduler as sch

CONFFILE = "config.ini"
CONF_DEFAULTS = {
    'loglevel': logging.INFO,
    'logfile' : 'mercury_client.log',
    'daemonize' : 0,
    'report_interval' : '10',
    'adapter_address' : '127.0.0.1',
    'adapter_port' : '8888',
}

#
# Mercury Client main class
#
class MercuryClient:
    def __init__(self):
        self.logger = None
        self.sched = sch.Scheduler()
        self.evhandler = eventhandler.EventHandler()
        self.udpi = udpiface.UDPInterface()
        self.session = session.ClientSession(self)
        self.cli_id = None
        self.adapter_addr = None
        self.adapter_port = None

    # Configure the logger and destination(s)
    def config_logger(self, config):
        self.logger = logging.getLogger("Mercury")
        self.logger.setLevel(logging.DEBUG)
        level = string.upper(config['Logging']['loglevel'])
        fmat = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        handler = None
        if bool(config['Client']['daemonize']):
            handler = logging.FileHandler(config['Logging']['logfile'])
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(fmat)
        handler.setLevel(level)
        self.logger.addHandler(handler)
        self.logger.info("log level set to: %s" % level)

    # Configure all the things based on input configuration file.
    def configure(self, confFile):
        config = configparser.SafeConfigParser(CONF_DEFAULTS)
        config.read(confFile)
        self.config = config['Client']
        self.config_logger(config)
        self.sched.configure(config)
        self.udpi.configure(self.config)
        self.session.configure(self.config)
        self.cli_id = self.config['client_id']
        self.adapter_addr = self.config['adapter_address']
        self.adapter_port = self.config['adapter_port']

    # Daemonize this thing!
    def daemonize(self):
        self.logger.info("Going into the background")
        pid = os.fork()
        if pid > 0:
            # exit first parent
            sys.exit(0)
        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

    def send_adapter_message(self, msg):
        self.udpi.send_msg(self.adapter_addr, int(self.adapter_port), msg)

    # Messages received here are from the udp listener, which serves
    # unicast udp clients.
    def process_udp_msg(self, ev):
        udpmsg = self.udpi.get_msg()
        (addr, port) = udpmsg[1]
        pmsg = mproto.MercuryMessage()
        pmsg.ParseFromString(udpmsg[0])
        if pmsg.type == mproto.MercuryMessage.AD_SESS:
            self.session.process_adapter_msg(pmsg)
        elif pmsg.type == mproto.MercuryMessage.PUB_CLI:
            print str(pmsg)
            pass
        else:
            self.logger.warning("Unexpected UDP message: Type: %s, Client address: %s:%s" % (pmsg.type, addr, port))


    # Start everything up!  Ultimately the scheduler and other
    # incoming events coordinate activities.
    def run(self):
        if bool(self.config['daemonize']):
            self.daemonize()
        self.udpi.bind()
        self.session.initialize()

        # Run forever.
        while True:
            self.evhandler.wait()
            while self.evhandler.hasevents():
                ev = self.evhandler.pop()
                self.logger.debug("Got event: %s" % ev.evtype)
                evswitch = {
                    sch.Scheduler.EVTYPE: lambda x: self.sched.check(),
                    udpiface.UDPInterface.EVTYPE: self.process_udp_msg,
                }
                def _bad(ev):
                    self.logger.warning("Unknown event type (ignored): %s" % ev.evtype)
                evfunc = evswitch.get(ev.evtype, _bad)
                evfunc(ev)

# Entry point
if __name__ == "__main__":
    MC = MercuryClient()
    MC.configure(CONFFILE)
    MC.run()
