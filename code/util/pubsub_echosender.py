#!/usr/bin/env python

import os, sys
import time
import array
import string
import logging
import threading
import json

import configparser

sys.path.append(os.path.abspath("../common"))
import eventhandler
import psubiface

CONFFILE = "echoconfig.ini"
CONF_DEFAULTS = {
    'loglevel': logging.INFO,
}

class PubSubEchoSender:
    LISTEN_TOPIC = 'EchoReply'
    SEND_TOPIC = 'EchoRequest'
    FINAL_WAIT_TIME = 5

    def __init__(self):
        self.logger = None
        self.evh = eventhandler.EventHandler()
        self.psubi = psubiface.PubSubInterface([PubSubEchoSender.LISTEN_TOPIC,])
        self.timings = array.array('f')
        self.rthr = threading.Thread(target=self.process_replies)
        self.rthr.daemon = True

    # Configure all the things based on input configuration file.
    def configure(self, confFile):
        config = configparser.SafeConfigParser(CONF_DEFAULTS)
        config.read(confFile)
        self.config = config['EchoSender']
        self.config_logger(config)
        self.psubi.configure(config)

    def config_logger(self, config):
        self.logger = logging.getLogger("Mercury")
        self.logger.setLevel(logging.DEBUG)
        level = string.upper(config['Logging']['loglevel'])
        fmat = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(fmat)
        handler.setLevel(level)
        self.logger.addHandler(handler)
        self.logger.info("log level set to: %s" % level)

    def run(self, count, rate):
        # Connect to pubsub.
        self.psubi.connect()
        # Fire up reply processor.
        self.rthr.start()
        # Send "count" echo messages.
        pgap = 1/rate
        stime = time.time()
        while count > 0:
            self.send_echo()
            time.sleep(pgap)
            count -= 1
        etime = time.time()
        self.logger.info("Total time taken: %f" % (etime - stime))

    def send_echo(self):
        attrs = { 'timestamp' : repr(time.time()) }
        self.psubi.send_msg(PubSubEchoSender.SEND_TOPIC, json.dumps(attrs))

    def process_replies(self):
        while True:
            self.evh.wait()
            while self.evh.hasevents():
                now = time.time()
                ev = self.evh.pop()
                self.logger.debug("Got event: %s" % ev.evtype)
                pmsg = self.psubi.get_msg()
                msgv = json.loads(pmsg.value.decode())
                pstamp = float(msgv['timestamp'])
                tdiff = now - pstamp
                self.timings.append(tdiff)

    def print_timings(self):
        for tm in self.timings:
            print tm

# Entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: pubsub_echosender.py <count> <rate>"
        sys.exit(1)
    count = int(sys.argv[1])
    rate = float(sys.argv[2])
    ES = PubSubEchoSender()
    ES.configure(CONFFILE)
    ES.run(count, rate)
    print "Waiting for final replies to come in."
    time.sleep(PubSubEchoSender.FINAL_WAIT_TIME)
    ES.print_timings()
