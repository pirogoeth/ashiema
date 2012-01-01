#!/usr/bin/env python

class User(object):
    def __init__(self, userstring):
        self.userstring = userstring
    
    def __repr__(self):
        return str(self.userstring)