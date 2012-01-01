#!/usr/bin/env python

""" represents a channel """

class Channel(object):
    def __init__(self, channel):
        self.name = channel
    
    def __repr__(self):
        return str(self.name)