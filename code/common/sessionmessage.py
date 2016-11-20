#!/usr/bin/env python

class TYPE:
    INIT   = "INIT"
    CLOSE  = "CLOSE"
    CLIREP = "CLIREP"
    HB     = "HB"

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
    NACK = "NACK"

class SessionMessage:
    def __init__(self, mtype):
        self.id = 0
        self.type = mtype
        self.kv = {}

    def getval(self, key):
        if key in self.kv:
            return kv[key]
        else:
            return None

    def add_kv(self, key, val):
        self.kv[key] = val
