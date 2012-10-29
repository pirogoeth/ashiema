#!/usr/bin/env python

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
    
    def to_s(self):
        return str(self.data)