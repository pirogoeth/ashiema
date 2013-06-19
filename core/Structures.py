#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import re, logging
import Connection

class Channel(object):

    __channels = {}

    def __init__(self, channel):

        self.connection = Connection.Connection.get_instance()
        self.name = channel

        if channel in Channel.__channels:
            self = Channel.__channels[channel]
        elif channel not in Channel.__channels:
            Channel.__channels[channel] = self
    
    def __repr__(self):

        return str(self.name)
    
    @staticmethod
    def join(channel, key = None):
        """ assembles a join message. """
        
        if key is None:
            message = "JOIN %s" % (channel)
        else: message = "JOIN %s :%s" % (channel, key)
        
        return message

    def to_s(self):

        return str(self.name)
    
    def is_self(self):

        return False
    
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

class User(object):
    
    def __init__(self, userstring):

        self.pattern = re.compile(r"""([^!].+)!(.+)@(.*)""", re.VERBOSE)

        self.connection = Connection.Connection.get_instance()
        self.userstring = userstring
        try: self.nick, self.ident, self.host = self.pattern.match(self.userstring).groups()
        except: self.nick = self.userstring
    
    def __repr__(self):

        return str(self.userstring)
    
    def __eq__(self, name):

        return str(self.nick) == name     
    
    def is_self(self):

        if self.nick == self.connection.nick:
            return True
        else:
            return False
    
    def message(self, *data):

        for slice in data:
            message = "PRIVMSG %s :%s" % (self.nick, slice)
            self.connection.send(message)
    
    privmsg = message
    
    def notice(self, data):

        message = "NOTICE %s :%s" % (self.nick, data)
        
        self.connection.send(message)
    
    def to_s(self):

        return str(self.userstring)