#!/usr/bin/env python

""" represents a channel """

class Channel(object):
    def __init__(self, connection, channel):
        self.connection = connection
        self.name = channel
    
    def __repr__(self):
        return str(self.name)
    
    def message(self, data):
        message = "PRIVMSG %s :%s" % (self.name, data)
    
        self.connection.send(message)
    privmsg = message
    
    def notice(self, data):
        message = "NOTICE %s :%s" % (self.name, data)
        
        self.connection.send(message)
    
    def set_topic(self, data):
        message = "TOPIC %s :%s" % (self.name, data)
        
        self.connection.send(message)