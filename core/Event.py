#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

""" this is an abstract class until tomorrow. """

class Event(object):
    """ this class is to be inherited and not directly instantiated and run. """
    
    def __init__(self, eventhandler, event_name):
        self.eventhandler = eventhandler
        self.name = event_name
        self.callbacks = {}
        
        self.get_thread = lambda func, data: threading.Thread(target = func, args = (data,))
        self.get_method_ident = lambda func: str(func.__module__) + str(func.__name__)

    def __repr__(self):
        return "<Event>"

    def __register__(self):
        self.eventhandler.register(self)

    def __unregister__(self):
        self.eventhandler.deregister(self)

    def __get_connection__(self):
        """ returns the connection instance """
        
        return self.connection

    def __get_eventhandler__(self):
        """ returns the event handler """
        
        return self.eventhandler
        
    def __get_name__(self):
        """ returns the identifiable name of the event. """
        
        return self.name

    def callback(self):
        """ registers a function to be run on the data. """
        def wrapper(function):
            def new(*args, **kw):
                self.callbacks[self.get_method_ident(function)] = function
            return new
        return wrapper
    
    def register(self, function):
        self.callbacks[self.get_method_ident(function)] = function

    def deregister(self, function):
        del self.callbacks[self.get_method_ident(function)]

    def match(self, data):
        """ this is a method that will provide the hooking system a mechanism
            to detect if a certain data value triggers a match on a registered
            event or not to help processing preservation. """
        
        pass

    def run(self, data):
        """ this provides a method to run when a line triggers an event.
            it must be overloaded. """
        
        pass
