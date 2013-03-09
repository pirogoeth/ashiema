#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

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
        try: return int(self.type)
        except (ValueError): return self.type