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

class PubSubEchoReplier:
    LISTEN_TOPIC = 'EchoRequest'
    SEND_TOPIC = 'EchoReply'

    def __init__(self):
        self.logger = None
        self.evh = eventhandler.EventHandler()
        self.psubi = psubiface.PubSubInterface([PubSubEchoReplier.LISTEN_TOPIC,])

    # Configure all the things based on input configuration file.
    def configure(self, confFile):
        config = configparser.SafeConfigParser(CONF_DEFAULTS)
        config.read(confFile)
        self.config = config['EchoReplier']
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

    def run(self):
        # Connect to pubsub.
        self.psubi.connect()
        # Run forever, replying to incoming echo requests.
        self.process_incoming()

    def process_incoming(self):
        while True:
            self.evh.wait()
            while self.evh.hasevents():
                now = time.time()
                ev = self.evh.pop()
                self.logger.debug("Got event: %s" % ev.evtype)
                pmsg = self.psubi.get_msg().value.decode()
                self.psubi.send_msg(PubSubEchoReplier.SEND_TOPIC, pmsg)

# Entry point
if __name__ == "__main__":
    ER = PubSubEchoReplier()
    ER.configure(CONFFILE)
    ER.run()
