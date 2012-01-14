#!/usr/bin/env python

import logging, util

class Plugin(object):
    """ this is the plugin implementation. """
    
    def __init__(self, connection, eventhandler):
        # you need to register events and commands and such right in here.
        
        self.connection = connection
        self.eventhandler = eventhandler
    
    def __deinit__(self):
        # you need to deregister events and commands right here. this will be called by the plugin loader.
        
        pass
    
    def get_connection(self):
        """ returns the connection object. """
        
        return self.connection
    
    def get_eventhandler(self):
        """ returns the eventhandler object """
        
        return self.eventhandler