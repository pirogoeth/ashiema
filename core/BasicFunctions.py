#!/usr/bin/env python

class Basic(object):
    """ provides the basic functions the bot needs """
    
    def __init__(self, connection):
        self.connection = connection
    
    def join(self, channel, key = None):
        """ allows the bot to join a channel """
        
        if key is None:
            message = 'JOIN %s' % (channel)
        else: message = 'JOIN %s :%s'
        
        self.connection.send(message)