#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import DefaultEvents, logging, traceback
from DefaultEvents import DefaultEventChainloader

class EventHandler(object):

    def __init__(self):
        self.events = {}
        self._d_loaded = False

    def __repr__(self):
        return "<EventHandler(%d events)>" % (len(self.events))

    def __call__(self):
        return self.events

    def load_default_events(self):
        """ loads all events necessary to perform basic functions """
        
        assert self._d_loaded is False, 'Default events have already been loaded.'

        self._dec = DefaultEventChainloader(self)
        logging.getLogger('ashiema').info("Loaded %d default events." % (self._dec.get_count()))

    def get_default_events(self):
        """ gets the default events for usage """
        
        return self._dec.get_events()
        
    def get_events(self):
        """ returns the events that have been loaded by the system. """
        
        return self.events

    def register(self, event):
        """ register an event in the handler """
        
        self.events.update({event.__get_name__(): event})
    
    def deregister(self, event):
        """ deregister an event from the handler """
        
        self.events.pop(event.__get_name__())
    
    def deregister_all(self):
        """ deregisters all events """
        
        [event.__deregister__() for event in self.events]
    
    def map_events(self, data):
        """ create a list of events that match the given data """
        
        e_map = []
        for event in self.get_events().values():
            if event.match(data):
                e_map.append(event)
            else: continue
        return self.fire(data, e_map)
    
    def fire(self, data, event_map):
        """ fire all mapped events with provided data """

        for event in event_map:
            try:
                event.run(data)
            except AssertionError, e:
                logging.getLogger('ashiema').error("assertion failed.")
                [logging.getLogger('ashiema').error('%s' % (trace)) for trace in traceback.format_exc(4).split('\n')]
            except Exception:
                [logging.getLogger('ashiema').error('%s' % (trace)) for trace in traceback.format_exc(4).split('\n')]

    def fire_once(self, event, data):
        try:
            event.run(data)
        except AssertionError, e:
            logging.getLogger('ashiema').error("assertion failed.")
            [logging.getLogger('ashiema').error('%s' % (trace)) for trace in traceback.format_exc(4).split('\n')]
        except Exception:
            [logging.getLogger('ashiema').error('%s' % (trace)) for trace in traceback.format_exc(4).split('\n')]