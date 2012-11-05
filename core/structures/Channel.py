#!/usr/bin/env python

""" represents a channel """

_channels = {}

class Channel(object):
    def __init__(self, connection, channel):
        self.connection = connection
        self.name = channel

        if channel in _channels:
            self = _channels[channel]
        elif channel not in _channels:
            _channels[channel] = self
    
    def __repr__(self):
        return str(self.name)
    
    def to_s(self):
        return str(self.name)
    
    def message(self, *data):
        for slice in data:
            message = "PRIVMSG %s :%s" % (self.name, slice)
            self.connection.send(message)

    privmsg = message
    
    def notice(self, data):
        message = "NOTICE %s :%s" % (self.name, data)
        
        self.connection.send(message)
    
    def set_topic(self, data):
        message = "TOPIC %s :%s" % (self.name, data)
        
        self.connection.send(message)
    
    def kick(self, user, reason = 'Your behaviour is not conductive to the desired environment'):
        message = "KICK %s %s :%s" % (self.name, user, reason)
        
        self.connection.send(message)