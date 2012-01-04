#!/usr/bin/env python

import DefaultEvents, logging
from DefaultEvents import DefaultEventChainloader

class EventHandler(object):

    def __init__(self, server):
        self.events = []
        self.server = server

    def __repr__(self):
        return "<EventHandler(%d events)>" % (len(self.events))

    def __call__(self):
        return self.events

    def load_default_events(self):
        """ loads all events necessary to perform basic functions """
        
        DefaultEventChainloader(self.server)
        logging.getLogger('ashiema').info("Loaded %d default events." % (len(self.events)))

    def register(self, event):
        """ register an event in the handler """
        
        self.events.append(event)
    
    def deregister(self, event):
        """ deregister an event from the handler """
        
        self.events.remove(event)
    
    def deregister_all(self):
        """ deregisters all events """
        
        [event.__deregister__() for event in self.events]
    
    def map_events(self, data):
        """ create a list of events that match the given data """
        
        e_map = []
        for event in self.events:
            if event.match(data):
                e_map.append(event)
            else: continue
        return self.fire(data, e_map)
    
    def fire(self, data, event_map):
        """ fire all mapped events with provided data """

        for event in event_map:
            event.run(data)