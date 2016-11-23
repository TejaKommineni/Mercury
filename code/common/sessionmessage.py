#!/usr/bin/env python

class CLIREP:
    X_LOC  = "x_location"
    Y_LOC  = "y_location"
    DIRECTION = "direction"
    SPEED = "speed"

class INIT:
    RESPONSE = "response"

class CLOSE:
    REASON = "reason"

class RV:
    SUCCESS = "SUCCESS"
    NOSESSION = "NOSESSION"

def get_msg_attr(msg, attr):
    smsg = msg.session_msg
    if hasattr(smsg, 'attributes'):
        for kv in smsg.attributes:
            if kv.key == attr:
                return kv.val
    return None

def add_msg_attr(msg, key, val):
    attr = msg.session_msg.attributes.add()
    attr.key = str(key)
    attr.val = str(val)
