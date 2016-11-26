#!/usr/bin/env python

import os, sys
import logging
import time

sys.path.append(os.path.abspath("../common"))
import mercury_pb2 as mproto
import pubsubmessage as psm

class ClientAppInterface(object):
    def __init__(self, client):
        self.logger = logging.getLogger("Mercury.AppInterface")
        self.client = client
        self.subs = {}

    def configure(self, config):
        self.config = config

    def process_app_msg(self, msg):
        app_id = msg.src_id.app_id
        appsw = {
            mproto.MercuryMessage.CLI_SUBSCR: self.handle_subscribe,
            mproto.MercuryMessage.CLI_UNSUB: self.handle_unsubscribe,
            mproto.MercuryMessage.CLI_PUB: self.handle_pubsub,
        }
        def _bad(msg):
            self.logger.warning("Unsupported message type from app %d: %s" %
                                int(msg.src_id.app_id), msg.type)
            return False
        hfunc = appsw.get(msg.type, _bad)
        return hfunc(msg)

    def process_pubsub(self, msg):
        topic = msg.pubsub_msg.topic
        if topic == psm.UTILITY.TYPES.ECHO:
            # FIXME: testing.
            self.logger.debug("\n" + str(msg))
        elif topic in psm.SAFETY.TYPES.TYPELIST and topic in self.subs:
            for app_id in self.subs[topic]:
                self.client.send_app_message(app_id, msg)
        else:
            if topic in self.subs:
                for app_id in self.subs[topic]:
                    self.client.send_app_message(app_id, msg)                

    def handle_subscribe(self, msg):
        app_id = msg.src_addr.app_id
        topic  = msg.pubsub_msg.topic
        self.logger.debug("Adding subscription to topic '%s' for app %d",
                          topic, int(app_id))
        if not topic in self.subs:
            self.subs[topic] = {}
            if topic not in psm.SAFETY.TYPES.TYPELIST:
                self.client.pubsub_subscribe(topic)
        self.subs[topic][app_id] = time.time()

    def handle_unsubscribe(self, msg):
        app_id = msg.src_addr.app_id
        topic  = msg.pubsub_msg.topic
        self.logger.debug("Removing subscription to topic '%s' for app %d",
                          topic, int(app_id))
        if topic in self.subs:
            if app_id in self.subs[topic]:
                del self.subs[topic][app_id]
                if not self.subs[topic] and topic not in \
                   psm.SAFETY.TYPES.TYPELIST:
                    self.client.pubsub_unsubscribe(topic)

    def handle_pubsub(self, msg):
        self.client.send_pubsub_message(self, msg)
