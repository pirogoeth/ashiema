#!/usr/bin/env python

class Type(object):
    def __init__(self, typedata):
        self.type = typedata
    
    def __repr__(self):
        return str(self.type)