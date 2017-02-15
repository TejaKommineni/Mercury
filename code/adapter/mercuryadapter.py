#!/usr/bin/env python

# Standard Python modules
import os, sys
import string
import logging
import json
import uuid
import copy
import threading

# Third party modules
import configparser

# Adapter-specific imports
import clientsession
import unicastclient as uc

# Common Mercury code
sys.path.append(os.path.abspath("../common"))
import psubiface
import udpiface
import eventhandler
import threadpool
import mercury_pb2 as mproto
import areaofinterest as aoi
import pubsubmessage as psm
import scheduler as sch

CONFFILE = "config.ini"
CONF_DEFAULTS = {
    'loglevel': logging.INFO,
    'logfile' : "mercury_adapter.log",
    'logtofile' : 0,
    'daemonize' : 0,
    'numthreads' : '10',
}

class CADDR_TYPES:
    UNICAST = "UNICAST"
    typelist = ['UNICAST']

class ClientAddresses:
    def __init__(self):
        self.cliaddrs = {}
        self.climap = {}
        self.lock = threading.Lock()
        for ctype in CADDR_TYPES.typelist:
            self.climap[ctype] = {}

    def add(self, cli_id, caddr):
        self.lock.acquire()
        self.cliaddrs[cli_id] = caddr
        self.climap[caddr.type][cli_id] = caddr
        self.lock.release()

    def delete(self, cli_id):
        self.lock.acquire()
        caddr = self.cliaddrs[cli_id]
        del self.climap[caddr.type][cli_id]
        del self.cliaddrs[cli_id]
        self.lock.release()

    def lookup(self, cli_id):
        addr = None
        self.lock.acquire()
        if cli_id in self.cliaddrs:
            addr = self.cliaddrs[cli_id]
        self.lock.release()
        return addr

    def alloftype(self, ctype):
        self.lock.acquire()
        rval = copy.deepcopy(self.climap[ctype].values())
        self.lock.release()
        return rval

#
# Main Mercury messaging adapter class
#
class MercuryAdapter:
    # Setup all the main functional components and pass them the
    # scheduler object.
    def __init__(self):
        self.logger = None
        self.thrpool = None
        self.sched = sch.Scheduler()
        self.evhandler = eventhandler.EventHandler()
        self.evhandler.setcallback(self.dispatch_event)
        self.psubi = psubiface.PubSubInterface(psm.BROKER_TOPICS.TOPICLIST)
        self.udpi = udpiface.UDPInterface()
        self.clitracker = clientsession.AdapterClientTracker(self)
        self.cliaddrs = ClientAddresses()

    # Configure the logger and destination(s)
    def config_logger(self, config):
        self.logger = logging.getLogger("Mercury")
        self.logger.setLevel(logging.DEBUG)
        level = string.upper(config['Logging']['loglevel'])
        fmat = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        handler = None
        if bool(config['Adapter']['daemonize']) or bool(config['Adapter']['logtofile']):
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
        numthr = int(self.config['numthreads'])
        self.logger.info("Initializing thread pool with %d threads" % numthr)
        self.thrpool = threadpool.ThreadPool(numthr)
        self.sched.configure(config)
        self.psubi.configure(config)
        self.udpi.configure(self.config)
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
        caddr = self.cliaddrs.lookup(cli_id)
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
            bcfunc(self.cliaddrs.alloftype(ctype), msg)

    # Send to clients based on AOI.
    # FIXME: Not structured for efficient address handling
    def send_cli_aoi(self, msg, aoi):
        clilist = self.clitracker.get_clients_in_aoi(aoi)
        for cli_id in clilist:
            caddr = self.cliaddrs.lookup(cli_id)
            if caddr.type == CADDR_TYPES.UNICAST:
                uc.send_msg(caddr, msg)

    # Send message to pubsub from client
    def send_pubsub_cli_msg(self, msg):
        pmsg = msg.pubsub_msg
        topic = pmsg.topic
        attrs = {'cli_id': msg.src_addr.cli_id}
        for kv in pmsg.attributes:
            attrs[kv.key] = kv.val
            if topic == psm.UTILITY.TYPES.ECHO and \
               kv.key == "Seq_Num":
                self.logger.debug("ekko request rcvd: seq %s" % kv.val)
        self.psubi.send_msg(topic, json.dumps(attrs))

    # Messages received here are from the udp listener, which serves
    # unicast udp clients.
    def process_udp_msg(self, ev):
        udpmsg = self.udpi.get_msg()
        (addr, port) = udpmsg[1]
        pmsg = mproto.MercuryMessage()
        pmsg.ParseFromString(udpmsg[0])
        cli_id = pmsg.src_addr.cli_id
        if pmsg.type == mproto.MercuryMessage.CLI_SESS:
            # Store address mapping for client and process.
            caddr = uc.ClientAddress(cli_id, addr, port)
            self.cliaddrs.add(cli_id, caddr)
            self.clitracker.process_sess_mesg(pmsg)
        elif pmsg.type == mproto.MercuryMessage.APP_CLI:
            # Store address mapping for client and process - sim client.
            caddr = uc.ClientAddress(cli_id, addr, port, dummy = True)
            self.cliaddrs.add(cli_id, caddr)
            self.clitracker.process_sess_mesg(pmsg)
        elif pmsg.type == mproto.MercuryMessage.CLI_PUB:
            if self.clitracker.check_session(pmsg):
                self.send_pubsub_cli_msg(pmsg)
            else:
                self.cliaddrs.delete(cli_id)
        else:
            self.logger.warning("Unexpected UDP message: Type: %s, Client address: %s:%s" % (pmsg.type, addr, port))

    # Messages incoming from the pubsub system.
    def process_psub_msg(self, ev):
        pmsg = self.psubi.get_msg()
        msgv = json.loads(pmsg.value.decode())
        if pmsg.topic == psm.SAFETY.BROKER_TOPIC:
            self.process_broker_safety_mesg(msgv)
        elif pmsg.topic == psm.UTILITY.BROKER_TOPIC:
            self.process_broker_utility_mesg(msgv)
        else:
            self.logger.warning("Unknown pubsub topic: %s" % topic)

    # Process safety message received from broker.
    def process_broker_safety_mesg(self, pmsg):
        if not pmsg.has_key('type'): return
        topic = pmsg['type']
        if not 'radius' in pmsg: pmsg['radius'] = 5
        bmsg = self._mk_broker_msg(topic)
        radarea = aoi.RadiusArea(pmsg['x_location'], pmsg['y_location'],
                                 pmsg['radius'])
        radarea.set_msg_geoaddr(bmsg)
        psm.add_msg_attr(bmsg, "message", pmsg['value'])
        self.logger.debug("Sending PubSub event to AOI")
        self.send_cli_aoi(bmsg.SerializeToString(), radarea)

    def process_broker_utility_mesg(self, pmsg):
        if not pmsg.has_key('type'): return
        topic = pmsg['type']
        if topic == psm.UTILITY.TYPES.ECHO:
            cli_id = pmsg['cli_id']
            if self.cliaddrs.lookup(cli_id):
                cmsg = self._mk_broker_msg(topic)
                cmsg.dst_addr.type = mproto.MercuryMessage.CLIENT
                cmsg.dst_addr.cli_id = int(cli_id)
                for k,v in pmsg.items():
                    if k == "Seq_Num":
                        self.logger.debug("ekko response rcvd: seq %s" % v)
                    psm.add_msg_attr(cmsg, k, v)
                self.send_cli_msg(cli_id, cmsg.SerializeToString())
        else:
            self.logger.warning("Unhandled utility message type from broker: %s" % topic)

    def _mk_broker_msg(self, topic):
        msg = mproto.MercuryMessage()
        #msg.uuid = str(uuid.uuid4())
        msg.type = mproto.MercuryMessage.PUB_CLI
        msg.src_addr.type = mproto.MercuryMessage.PUBSUB
        msg.pubsub_msg.topic = topic
        return msg

    # Actually figure out what to do with event in thread.
    def _process_event(self, ev):
        self.logger.debug("Got event: %s" % ev.evtype)
        evswitch = {
            sch.Scheduler.EVTYPE: lambda x: self.sched.check(),
            udpiface.UDPInterface.EVTYPE: self.process_udp_msg,
            psubiface.PubSubInterface.EVTYPE: self.process_psub_msg,
        }
        def _bad(ev):
            self.logger.warning("Unknown event type (ignored): %s" % ev.evtype)
        evfunc = evswitch.get(ev.evtype, _bad)
        evfunc(ev)

    # Dispatch event processing.
    def dispatch_event(self, ev):
        self.thrpool.add_task(self._process_event, ev)

    # Start everything up!  Ultimately the scheduler and other
    # incoming events coordinate activities via the thread pool.
    def run(self):
        if bool(self.config['daemonize']):
            self.daemonize()
        self.clitracker.start()
        self.psubi.connect()
        self.udpi.bind()
        
        # Run forever.
        self.thrpool.join_all()

# Entry point
if __name__ == "__main__":
    MA = MercuryAdapter()
    MA.configure(CONFFILE)
    MA.run()
