#!/usr/bin/env python

class Type(object):
    def __init__(self, typedata):
        self.type = typedata
    
    def __repr__(self):
        return str(self.type)
    
    def __call__(self):
        return str(self.type)
    
    def to_s(self):
        return str(self.type)
        
    def to_i(self):
        return int(self.type)