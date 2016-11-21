#!/usr/bin/env python
import os, sys
import string
import configparser
import logging
import json

import psubiface
import udpiface
import clitracker
import eventhandler
import clientaddress as ca

sys.path.append(os.path.abspath("../common"))
import mercury_pb2 as mproto
from scheduler import Scheduler

CONFFILE = "config.ini"
CONF_DEFAULTS = {
    'loglevel': logging.INFO,
    'logfile' : "mercury_adapter.log",
    'daemonize' : 0,
}

#
# Main Mercury messaging adapter class
#
class MercuryAdapter:
    # Setup all the main functional components and pass them the
    # scheduler object.
    def __init__(self):
        self.logger = None
        self.sched = Scheduler()
        self.evhandler = eventhandler.AdapterEventHandler()
        self.psubi = psubiface.AdapterPubSubInterface()
        self.udpi = udpiface.AdapterUDPInterface()
        self.clitracker = clitracker.AdapterClientTracker(self)
        self.climap = {}

    # Configure the logger and destination(s)
    def config_logger(self, config):
        self.logger = logging.getLogger("Mercury")
        self.logger.setLevel(logging.DEBUG)
        level = string.upper(config['Logging']['loglevel'])
        fmat = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        handler = None
        if bool(config['Adapter']['daemonize']):
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
        self.config = config['Adapter']
        self.config_logger(config)
        self.sched.configure(config)
        self.psubi.configure(config)
        self.udpi.configure(config)
        self.clitracker.configure(config)

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

    def _send_cli_udp_msg(self, caddr, msg):
        return self.udpi.send_msg(caddr.address, caddr.port, msg)

    def send_broker_cli_msg(self, cli_id, msg):
        self.psubi.send_msg("Client_Report", json.dumps(msg.__dict__))
    
    def send_cli_msg(self, cli_id, msg):
        smsg = msg.SerializeToString()
        caddr = self.climap[cli_id]
        clisw = {
            ca.CADDR_TYPES.UDP: self._send_cli_udp_msg,
        }
        def _bad(caddr, dummy):
            self.logger.warning("Can't handle client %d: type %s" %
                                (int(caddr.cli_id), caddr.type))
            return False
        sendfunc = clisw.get(caddr.type, _bad)
        return sendfunc(caddr, smsg)
        
    def process_udp_msg(self, ev):
        udpmsg = self.udpi.get_msg()
        (addr, port) = udpmsg[1]
        pmsg = mproto.MercuryMessage()
        pmsg.ParseFromString(udpmsg[0])
        if pmsg.type == mproto.MercuryMessage.CLI_SESS:
            # Store address mapping for client and process.
            cli_id = pmsg.src_addr.cli_id
            self.climap[cli_id] = ca.UDPClientAddress(cli_id, addr, port)
            self.clitracker.process_sess_mesg(pmsg)
        else:
            self.logger.warning("Unexpected UDP message: Type: %s, Client address: %s:%s" % (pmsg.type, addr, port))
            return

    # Start everything up!  Ultimately the scheduler and other
    # incoming events coordinate activities.
    def run(self):
        if bool(self.config['daemonize']):
            self.daemonize()
        self.clitracker.start()
        self.psubi.connect()
        self.udpi.bind()
        
        # Run forever.
        while True:
            self.evhandler.wait()
            # FIXME: Process more events!
            while self.evhandler.hasevents():
                ev = self.evhandler.pop()
                self.logger.debug("Got event: %s" % ev.evtype)
                evswitch = {
                    Scheduler.EVTYPE: lambda x: self.sched.check(),
                    udpiface.AdapterUDPInterface.EVTYPE: self.process_udp_msg,
                }
                def _unknown_event(ev):
                    self.logger.warning("Unknown event (ignored): %s" % ev.evtype)
                evfunc = evswitch.get(ev.evtype, _unknown_event)
                evfunc(ev)

# Entry point
if __name__ == "__main__":
    MA = MercuryAdapter()
    MA.configure(CONFFILE)
    MA.run()
