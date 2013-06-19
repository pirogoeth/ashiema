#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import re, logging, traceback
import Connection, EventHandler, Structures

class Tokenizer(object):
    """ convert a line into a fielded object """

    @staticmethod
    def process_events(data):
        
        EventHandler.EventHandler.get_instance().map_events(data)

    def __init__(self, data):

        self._raw = data
        self.connection = Connection.Connection.get_instance()
        self.eventhandler = EventHandler.EventHandler.get_instance()
        # this regular expression splits an IRC line up into four parts:
        # ORIGIN, TYPE, TARGET, MESSAGE
        regex = "^(?:\:([^\s]+)\s)?([A-Za-z0-9]+)\s(?:([^\s\:]+)\s)?(?:\:?(.*))?$"
        # a regular expression to match and dissect IRC protocol messages
        # this is around 60% faster than not using a RE
        p = re.compile(regex, re.VERBOSE)
        try:
            self.origin, self.type, self.target, self.message = (None, None, None, None)
            self._origin, self._type, self._target, self._message = p.match(data).groups()
            # take each token and initialise the appropriate structure.
            self.origin = Structures.User(self._origin) if self._origin is not None else None
            self.type = Structures.Type(self._type) if self._type is not None else None
            if self._target.startswith('#', 0, 1) is True:
                self.target = Structures.Channel(self._target) if self._target is not None else None
            else: self.target = Structures.User(self._target) if self._target is not None else None
            self.message = Structures.Message(self._message)
        except (AttributeError):
            pass
        try:
            if logging.getLogger('ashiema').getEffectiveLevel() is logging.DEBUG and self.connection.debug is True:
                if self.type and self.message:
                    logging.getLogger('ashiema').debug("%s %s %s %s" % (str(self.origin), str(self.type), str(self.target), str(self.message)))
        except:
            [logging.getLogger('ashiema').error(trace) for trace in traceback.format_exc(5).split('\n')]
            pass
    
    def get_raw(self):

        return self._raw
    
    def respond_to_user(self, message, prefer_notice = True):

        if self.target.is_self():
            if prefer_notice:
                self.origin.notice(message)
            else:
                self.origin.message(message)
        else:
            self.target.message(message)
            