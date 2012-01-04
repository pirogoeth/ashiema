#!/usr/bin/env python

""" this is an abstract class until tomorrow. """

class Event(object):
    """ this class is to be inherited and not directly instantiated and run. """
    
    def __init__(self, instance):
        self.connection = instance
        self.eventhandler = instance._evh

    def __repr__(self):
        return "<Event>"

    def __register__(self):
        self.eventhandler.register(self)

    def __unregister__(self):
        self.eventhandler.deregister(self)

    def __get_connection__(self):
        """ returns the connection instance """
        
        return self.connection

    def __get_event__(self):
        """ returns the event handler """
        
        return self.eventhandler

    def match(self, data):
        """ this is a method that will provide the hooking system a mechanism
            to detect if a certain data value triggers a match on a registered
            event or not to help processing preservation. """
        
        pass

    def run(self, data):
        """ this provides a method to run when a line triggers an event.
            it must be overloaded. """
        
        pass
