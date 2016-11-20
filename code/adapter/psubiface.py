#!/usr/bin/env python

import threading
from kafka import KafkaConsumer, KafkaProducer, TopicPartition

TOPICLIST = ['Message_Broker',]

class AdapterPubSubInterface:
    def __init__(self):
        self.producer = None
        self.consumer_thread = None
        self.topiclist = []
        self.topiclock = threading.Lock()
        for topic in TOPICLIST:
            self._add_topic(topic)
        self.msglist = []
        self.msglock = threading.Lock()

    def configure(self, config):
        self.psconfig = config['PubSub']
        self.config   = config['Adapter']

    def _add_topic(self, new_topic):
        self.topiclock.acquire()
        self.topiclist.append(TopicPartition(new_topic, 0))
        self.topiclock.release()

    def connect(self):
        self.consumer_thread = threading.Thread(target=self.run_consumer)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
        self.producer = KafkaProducer(bootstrap_servers=[self.psconfig['bootstrap_server']])

    def _add_msg(self, msg):
        self.msglock.acquire()
        self.msglist.append(msg)
        self.msglock.release()

    def run_consumer(self):
        self.consumer = KafkaConsumer(bootstrap_servers=[self.psconfig['bootstrap_server']])
        self.consumer.assign(self.topiclist)
        for msg in self.consumer:
            print "got one!"
            self._add_msg(msg)

    def get_msg(self):
        msg = None
        self.msglock.acquire()
        if len(self.msglist):
            msg = self.msglist.pop()
        self.msglock.release()
        return msg

    def send_msg(self, topic, msg):
        self.producer.send(topic, msg.encode())
