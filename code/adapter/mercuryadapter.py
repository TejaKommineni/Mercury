#!/usr/bin/env python
import os, sys
import string
import configparser
import logging

import psubiface
import udpiface
import clitracker
import eventhandler

sys.path.append(os.path.abspath("../common"))
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
        self.cli = clitracker.AdapterClientTracker(self)

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
        self.cli.configure(config)

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

    # Start everything up!  Ultimately the scheduler and other
    # incoming events coordinate activities.
    def run(self):
        self.sched.start()
        if bool(self.config['daemonize']):
            self.daemonize()
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
