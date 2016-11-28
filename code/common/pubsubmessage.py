#!/usr/bin/env python

class SAFETY:
    BROKER_TOPIC = "Broker_Safety"
    
    class TYPES:
        COLLISION  = "Collision"
        CONGESTION = "Congestion"
        EMERGENCY  = "Emergency"
        MOVINGOBJ  = "Moving_Objects"
        OBSTACLE   = "Obstacle"
        BLOCKED    = "Blocked"
        LCHANGE    = "Lane_Change_Assistance"
        ALL        = "_All_Safety_"

    class ATTRIBUTES:
        X_LOC      = "x_location"
        Y_LOC      = "y_location"
        RADIUS     = "radius"
        
    TYPELIST = [TYPES.COLLISION, TYPES.CONGESTION, TYPES.EMERGENCY,
                TYPES.MOVINGOBJ, TYPES.OBSTACLE, TYPES.BLOCKED, TYPES.LCHANGE,
                TYPES.ALL]

class UTILITY:
    BROKER_TOPIC = "Broker_Utility"

    class TYPES:
        ECHO = "Echo"

    class ATTRIBUTES:
        APP_ID     = "App_ID"
        ECHO_STAMP = "Echo_Stamp"

    TYPELIST = [TYPES.ECHO,]

class BROKER_TOPICS:
    TOPICLIST = [SAFETY.BROKER_TOPIC, UTILITY.BROKER_TOPIC]
    
def get_msg_attr(msg, attr):
    pmsg = msg.pubsub_msg
    if hasattr(pmsg, 'attributes'):
        for kv in pmsg.attributes:
            if kv.key == attr:
                return kv.val
    return None

def add_msg_attr(msg, key, val):
    attr = msg.pubsub_msg.attributes.add()
    attr.key = str(key)
    attr.val = str(val)
