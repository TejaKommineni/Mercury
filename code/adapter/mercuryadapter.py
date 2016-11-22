#!/usr/bin/env python
import os, sys
import string
import logging
import json
import uuid

import configparser

import psubiface
import udpiface
import clientsession
import unicastclient as uc

sys.path.append(os.path.abspath("../common"))
import eventhandler
import mercury_pb2 as mproto
import areaofinterest as aoi
import pubsubmessage as psm
import scheduler as sch

CONFFILE = "config.ini"
CONF_DEFAULTS = {
    'loglevel': logging.INFO,
    'logfile' : "mercury_adapter.log",
    'daemonize' : 0,
}

class CADDR_TYPES:
    UNICAST = "UNICAST"
    typelist = ['UNICAST']

#
# Main Mercury messaging adapter class
#
class MercuryAdapter:
    # Setup all the main functional components and pass them the
    # scheduler object.
    def __init__(self):
        self.logger = None
        self.sched = sch.Scheduler()
        self.evhandler = eventhandler.EventHandler()
        self.psubi = psubiface.AdapterPubSubInterface()
        self.udpi = udpiface.AdapterUDPInterface()
        self.clitracker = clientsession.AdapterClientTracker(self)
        self.cliaddrs = {}
        self.climap = {}
        for ctype in CADDR_TYPES.typelist:
            self.climap[ctype] = {}

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

    # Send client report across pubsub to broker.
    def send_broker_cli_report(self, cli_id, msg):
        self.psubi.send_msg("Client_Report", json.dumps(msg.__dict__))

    # Send to just one client
    def send_cli_msg(self, cli_id, msg):
        caddr = self.cliaddrs[cli_id]
        clisw = {
            CADDR_TYPES.UNICAST: uc.send_msg,
        }
        def _bad(caddr, dummy):
            self.logger.warning("Can't handle client %d: type %s" %
                                (int(caddr.cli_id), caddr.type))
            return False
        sendfunc = clisw.get(caddr.type, _bad)
        return sendfunc(caddr, msg)

    # Send to all clients!
    def send_cli_bcast(self, msg):
        clisw = {
            CADDR_TYPES.UNICAST: uc.send_bcast
        }
        def _bad(clist, msg):
            self.logger.warning("Unhandled client address type!")
        for ctype in CADDR_TYPES.typelist:
            bcfunc = clisw.get(ctype, _bad)
            bcfunc(self.climap[ctype].values(), msg)

    # Send to clients based on AOI.
    # FIXME: Not structured for efficient address handling
    def send_cli_aoi(self, msg, aoi):
        clilist = self.clitracker.get_clients_in_aoi(aoi)
        for cli_id in clilist:
            caddr = self.cliaddrs[cli_id]
            if caddr.type == CADDR_TYPES.UNICAST:
                uc.send_msg(caddr, msg)

    # Send message to pubsub from client
    def send_pubsub_cli_msg(msg):
        pmsg = msg.pubsub_msg
        topic = pmsg.topic
        attrs = {}
        for kv in pmsg.attributes:
            attrs[kv.key] = kv.val
        self.psubi.send_msg(topic, json.dumps(attrs))

    # Messages received here are from the udp listener, which serves
    # unicast udp clients.
    def process_udp_msg(self, ev):
        udpmsg = self.udpi.get_msg()
        (addr, port) = udpmsg[1]
        pmsg = mproto.MercuryMessage()
        pmsg.ParseFromString(udpmsg[0])
        if pmsg.type == mproto.MercuryMessage.CLI_SESS:
            # Store address mapping for client and process.
            cli_id = pmsg.src_addr.cli_id
            addr = uc.ClientAddress(cli_id, addr, port)
            self.cliaddrs[cli_id] = addr
            self.climap[CADDR_TYPES.UNICAST][cli_id] = addr
            self.clitracker.process_sess_mesg(pmsg)
        if pmsg.type == mproto.MercuryMessage.CLI_PUB:
            if self.clitracker.check_session(pmsg):
                self.send_pubsub_cli_msg(pmsg)
        else:
            self.logger.warning("Unexpected UDP message: Type: %s, Client address: %s:%s" % (pmsg.type, addr, port))

    # Messages incoming from the pubsub system.
    def process_psub_msg(self, ev):
        pmsg = self.psubi.get_msg()
        if pmsg.topic == "Message_Broker":
            msg = json.loads(pmsg.value.decode())
            self.process_broker_mesg(msg)
        else:
            self.logger.warning("Unknown pubsub topic: %s" % topic)

    # Process message received from broker.
    def process_broker_mesg(self, pmsg):
        # FIXME: Broker is not currently sending along a message type, so
        #        just treat all messages as AOI radius safety broadcasts 
        #        for now.
        #
        # FIXME: The 'geo_mat' destination format needs more thought.
        bmsg = self._mk_broker_safety_msg()
        bmsg.dst_addr.geo_mat = "type:radius,x_location:%s,y_location:%s,radius=%s" % (pmsg['x_location'], pmsg['y_location'], pmsg['radius'])
        psm.add_msg_attr(bmsg, psm.SAFETY.MSG, pmsg['value'])
        radarea = aoi.RadiusArea(pmsg['x_location'], pmsg['y_location'],
                                 pmsg['radius'])
        self.send_cli_aoi(bmsg.SerializeToString(), radarea)

    def _mk_broker_safety_msg(self):
        msg = mproto.MercuryMessage()
        msg.uuid = str(uuid.uuid4())
        msg.type = mproto.MercuryMessage.PUB_CLI
        msg.src_addr.type = mproto.MercuryMessage.PUBSUB
        msg.dst_addr.type = mproto.MercuryMessage.GEO
        msg.pubsub_msg.topic = psm.TOPICS.SAFETY
        return msg
        
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
            while self.evhandler.hasevents():
                ev = self.evhandler.pop()
                self.logger.debug("Got event: %s" % ev.evtype)
                evswitch = {
                    sch.Scheduler.EVTYPE: lambda x: self.sched.check(),
                    udpiface.AdapterUDPInterface.EVTYPE: self.process_udp_msg,
                    psubiface.AdapterPubSubInterface.EVTYPE: self.process_psub_msg,
                }
                def _bad(ev):
                    self.logger.warning("Unknown event type (ignored): %s" % ev.evtype)
                evfunc = evswitch.get(ev.evtype, _bad)
                evfunc(ev)

# Entry point
if __name__ == "__main__":
    MA = MercuryAdapter()
    MA.configure(CONFFILE)
    MA.run()