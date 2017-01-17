#!/usr/bin/env python
    
def get_msg_attr(msg, attr):
    amsg = msg.appcli_msg
    if hasattr(amsg, 'attributes'):
        for kv in amsg.attributes:
            if kv.key == attr:
                return kv.val
    return None

def add_msg_attr(msg, key, val):
    attr = msg.appcli_msg.attributes.add()
    attr.key = str(key)
    attr.val = str(val)
    return attr
