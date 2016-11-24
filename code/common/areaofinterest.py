#!/usr/bin/env python

import os, sys
import math

sys.path.append(os.path.abspath("../common"))
import mercury_pb2 as mproto

class AOI_TYPES:
    RADIUS = "RADIUS"
    
class AreaOfInterest(object):
    def __init__(self, aoi_type):
        self.type = aoi_type

def add_geoaddr_attr(msg, key, val):
    attr = msg.dst_addr.geo_addr.attributes.add()
    attr.key = str(key)
    attr.val = str(val)

class RadiusArea(AreaOfInterest):
    def __init__(self, x, y, r):
        super(RadiusArea, self).__init__(AOI_TYPES.RADIUS)
        self.x = int(x)
        self.y = int(y)
        self.r = int(r)

    def in_aoi(self, x, y):
        dist = math.sqrt((int(x) - self.x)**2 + (int(y) - self.y)**2)
        if dist <= self.r:
            return True
        return False

    def set_msg_geoaddr(self, msg):
        msg.dst_addr.type = mproto.MercuryMessage.GEO
        msg.dst_addr.geo_addr.type = AOI_TYPES.RADIUS
        add_geoaddr_attr(msg, "x_location", self.x)
        add_geoaddr_attr(msg, "y_location", self.y)
        add_geoaddr_attr(msg, "radius", self.r)
