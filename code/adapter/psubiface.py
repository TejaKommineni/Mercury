#!/usr/bin/env python

from kafka import KafkaConsumer, KafkaProducer

class AdapterPubSubInterface:
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def configure(self, config):
        self.config = config

    
