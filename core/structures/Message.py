#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

class Message(object):
    def __init__(self, data):
        self.data = data
    
    def __call__(self):
        return self.data.split()
    
    def __repr__(self):
        return str(self.data)
    
    def __eq__(self, (index, cmp)):
        return self()[index] == cmp
    
    def __ne__(self, (index, cmp)):
        return self()[index] != cmp
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, index):
        return self()[index]
    
    def split(self, delim):
        return self.data.split(delim)
        
    def contains(self, value):
        return value in self.to_s()
    
    def has_index(self, index):
        try:
            if self.data.split()[index]:
                return True
            else:
                return False
        except (IndexError):
            return False
    
    def raw(self):
        return self.data
    
    def to_s(self):
        return str(self.data)