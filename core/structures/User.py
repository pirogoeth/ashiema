#!/usr/bin/env python

import re

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