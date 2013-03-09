#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import logging, util, os, errno

class Plugin(object):
    """ this is the plugin implementation. """
    
    def __init__(self, connection, eventhandler, needs_dir = False):
        # you need to register events and commands and such right in here.
        
        self.connection = connection
        self.eventhandler = eventhandler
        
        self.path = os.getcwd() + "/plugins/" + type(self).__name__ + "/"
        
        # set up the plugins directory, if it doesn't exist.
        if not os.path.exists(self.path) and needs_dir:
            try:
                os.makedirs(self.path)
            except OSError as e:
                if exception.errno != errno.EEXIST:
                    raise
    
    def __deinit__(self):
        # you need to deregister events and commands right here. this will be called by the plugin loader.
        
        pass
    
    def get_connection(self):
        """ returns the connection object. """
        
        return self.connection
    
    def get_eventhandler(self):
        """ returns the eventhandler object """
        
        return self.eventhandler
    
    def get_path(self):
        """ returns the plugin directory path. """
        
        return self.path