#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

class Basic(object):
    """ provides the basic functions the bot needs """
    
    def __init__(self, connection):
        self.connection = connection
    
    def join(self, channel, key = None):
        """ allows the bot to join a channel """
        
        if key is None:
            message = 'JOIN %s' % (channel)
        else: message = 'JOIN %s :%s' % (channel, key)
        
        self.connection.send(message)