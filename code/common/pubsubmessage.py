#!/usr/bin/env python

class TOPICS:
    SAFETY = "SAFETY_ALERT"

class SAFETY:
    MSG = "message"

def get_msg_attr(msg, attr):
    pmsg = msg.pubsub_msg
    if hasattr(pmsg, 'attributes'):
        for kv in pmsg.attributes:
            if kv.key == attr:
                return kv.val
    return None

def add_msg_attr(msg, key, val):
    attr = msg.pubsub_msg.attributes.add()
    attr.key = key
    attr.val = val
