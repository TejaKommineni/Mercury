#!/usr/bin/env python

import math

class AOI_TYPES:
    RADIUS = "RADIUS"
    
class AreaOfInterest(object):
    def __init__(self, aoi_type):
        self.type = aoi_type

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
