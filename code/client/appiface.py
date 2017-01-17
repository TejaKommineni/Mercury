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
        self.subs[psm.SAFETY.TYPES.ALL] = {}

    def configure(self, config):
        self.config = config

    def process_app_msg(self, msg):
        app_id = msg.src_addr.app_id
        appsw = {
            mproto.MercuryMessage.APP_CLI: self.handle_appcli,
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
        self.logger.debug("Received pubsub event, topic: %s" % topic)
        if topic == psm.UTILITY.TYPES.ECHO:
            app_id = psm.get_msg_attr(msg, psm.UTILITY.ATTRIBUTES.APP_ID)
            self.client.send_app_message(int(app_id), msg)
        elif topic in psm.SAFETY.TYPELIST:
            if topic in self.subs:
                for app_id in self.subs[topic]:
                    self.client.send_app_message(app_id, msg)
            for app_id in self.subs[psm.SAFETY.TYPES.ALL]:
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
            if topic not in psm.SAFETY.TYPELIST:
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
        app_id = int(msg.src_addr.app_id)
        self.logger.debug("Sending app message to pubsub, app_id: %d",
                          app_id)
        self.client.send_pubsub_message(msg)

    def handle_appcli(self, msg):
        app_id = int(msg.src_addr.app_id)
        if msg.appcli_msg.type == psm.UTILITY.TYPES.ECHO:
            self.logger.debug("Responding to app echo request, app_id: %d", 
                              app_id)
            msg.type = mproto.MercuryMessage.CLI_APP
            msg.src_addr.type = mproto.MercuryMessage.CLIENT
            msg.src_addr.cli_id = int(self.client.cli_id)
            msg.dst_addr.type = mproto.MercuryMessage.APP
            msg.dst_addr.app_id = app_id
            self.client.send_app_message(app_id, msg)
        elif msg.appcli_msg.type == psm.UTILITY.TYPES.ECHO_ADAPTER:
            self.logger.debug("Sending echo request toward adapter, app_id: %d", 
                              app_id)
            msg.type = mproto.MercuryMessage.CLI_SESS
            msg.src_addr.type = mproto.MercuryMessage.CLIENT
            msg.src_addr.cli_id = int(self.client.cli_id)
            msg.dst_addr.type = mproto.MercuryMessage.ADAPTER
            msg.session_msg.type = mproto.SessionMsg.ECHO
            self.client.send_adapter_message(msg.SerializeToString())
        else:
            self.logger.warning("Ignoring unknown application message type: %s" % msg.appcli_msg.type)
