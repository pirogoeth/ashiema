#!/usr/bin/env python

class User(object):
    def __init__(self, connection, userstring):
        self.connection = connection
        self.userstring = userstring
        self.nick, self.ident, self.host = (None, None, None)
        try:
            self.nick = self.userstring.split('!')[0]
            self.ident = self.userstring.split('!').split('@')[0]
            self.host = self.userstring.split('@')[1]
        except: pass
    
    def __repr__(self):
        return str(self.userstring)
    
    def message(self, data):
        message = "PRIVMSG %s :%s" % (self.nick, data)
        
        self.connection.send(message)
    
    def notice(self, data):
        message = "NOTICE %s :%s" % (self.nick, data)
        
        self.connection.send(message)