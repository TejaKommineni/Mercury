#!/usr/bin/env python
import os, sys
import configparser
import logging

import scheduler
import psubiface
import udpiface
import clitracker

CONFFILE = "config.ini"
CONF_DEFAULTS = {
    'loglevel': logging.INFO,
    'logfile' : "%s.log" % __name__,
    'daemonize' : 0,
    'gc_interval' : 30
}

#
# Main Mercury messaging adapter class
#
class MercuryAdapter:
    # Setup all the main functional components and pass them the
    # scheduler object.
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sched = scheduler.Sheduler()
        self.psubi = psubiface.AdapterPubSubInterface(self.sched)
        self.udpi = udpiface.AdapterUDPInterface(self.sched)
        self.cli = clitracker.AdapterClientTracker(self.sched)

    # Configure all the things based on input configuration file.
    def configure(self, confFile):
        config = configparser.SafeConfigParser(CONF_DEFAULTS)
        config.read(confFile)
        self.config = config['Adapter']
        logging.basicConfig(level=int(self.config['loglevel']), filename=self.config['logfile'])
        self.logger.info("log level set to: %s" % logging.getLevelName(int(self.config['loglevel'])))
        self.sched.configure(config)
        self.psubi.configure(config)
        self.udpi.configure(config)
        self.cli.configure(config)

    # Daemonize this thing!
    def daemonize(self):
        self.logger.info("Going into the background")
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            self.logger.error("fork failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
    # Do garbage collection tasks (nothing here yet!)
    def doGC(self):
        pass

    # Start everything up!  Ultimately the scheduler and other
    # incoming events coordinate activities.
    def run(self):
        if bool(self.config['daemonize']) != False:
            self.daemonize()
        self.psubi.connect()
        self.udpi.bind()
        self.sched.periodic(self.config['gc_interval'], self.doGC())
        self.sched.run()
        pass
        
if __name__ == "main":
    MercuryAdapter MA = MercuryAdapter()
    MA.configure(CONFFILE)
    MA.run()
