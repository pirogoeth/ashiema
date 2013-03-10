#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import re, logging

class User(object):
    def __init__(self, connection, userstring):
        # re pattern
        self.pattern = re.compile(r"""([^!].+)!(.+)@(.*)""", re.VERBOSE)
        # everything else
        self.connection = connection
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