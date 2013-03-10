#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import Event, logging, time, threading, core
from Event import Event
from core import get_connection

get_thread = lambda func, data: threading.Thread(target = func, args = (data,))
get_method_ident = lambda func: str(func.__module__) + str(func.__name__)

class DefaultEventChainloader(object):
    """ this chainloads all default events """
    
    def __init__(self, eventhandler):
        self.defaults = {
            'RFCEvent': RFCEvent(eventhandler), # mainly server triggered events
            'PingEvent': PingEvent(eventhandler),
            'ErrorEvent': ErrorEvent(eventhandler),
            'ModeChangeEvent': ModeChangeEvent(eventhandler),
            'MessageEvent': MessageEvent(eventhandler), # user triggered events
            'PMEvent': PMEvent(eventhandler),
            'JoinEvent': UserJoinedEvent(eventhandler),
            'PartEvent': UserPartedEvent(eventhandler),
            'QuitEvent': UserQuitEvent(eventhandler),
            'PluginsLoadedEvent': PluginsLoadedEvent(eventhandler) # system triggered events
        }
    
    def get_events(self):
        return self.defaults
    
    def get_count(self):
        return len(self.defaults)

class BasicUserEvent(Event):

    def __init__(self, eventhandler, event_name = "BasicUserEvent"):
        Event.__init__(self, eventhandler, event_name)
        self.__register__()
    
    def match(self, data):
        pass
    
    def run(self, data):
        if self.callbacks is not None:
            for function in self.callbacks.values():
                thread = get_thread(function, data)
                thread.setDaemon(True)
                thread.start()


class PluginsLoadedEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler, "PluginsLoadedEvent")
        self.__register__()

    def match(self, data = None):
        return get_connection().pluginloader._loaded
    
    def run(self, data = None):
        for callback in self.callbacks.values():
            callback()

class ModeChangeEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler, "ModeChangeEvent")
        self.__register__()
        self.commands = ['MODE', 'OMODE', 'UMODE']
    
    def match(self, data = None):
        if self.commands.__contains__(str(data.type)) and data.target == data.connection.nick:
            return True
        return False
    
    def run(self, data):
        if self.callbacks is not None:
            for function in self.callbacks.values():
                thread = get_thread(function, data)
                thread.setDaemon(True)
                thread.start()

class ErrorEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler, "ErrorEvent")
        self.__register__()
    
    def match(self, data):
        if (str(data.type) == "ERROR" or str(data.type) == "KILL") and data.message:
            return True
    
    def run(self, data):
        logging.getLogger('ashiema').critical('<- %s: %s' % (str(data.type), data.message))
        # adjust the loop shutdown flag
        data.connection.shutdown()

class PMEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler, "PMEvent")
        self.__register__()
        self.commands = ['PRIVMSG']

    def match(self, data):
        if self.commands.__contains__(str(data.type)) and str(data.target) == data.connection.nick:
            return True

    def run(self, data):
        if self.callbacks is not None:
            for function in self.callbacks.values():
                thread = get_thread(function, data)
                thread.setDaemon(True)
                thread.start()

class RFCEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler, "RFCEvent")
        self.__register__()
    
    def match(self, data):
        try:
            if len(str(data.type)) is 3:
                return True
        except (ValueError): return False

    def run(self, data):
        if data.type.to_i() == 001:
            # RPL_WELCOME
            logging.getLogger('ashiema').info('<- welcome received: %s' % (data.message))
        elif data.type.to_i() == 002:
            # RPL_YOURHOST
            logging.getLogger('ashiema').info('<- %s' % (data.message))
        elif data.type.to_i() == 353:
            # RPL_NAMREPLY
            pass
        elif data.type.to_i() == 376:
            # RPL_ENDOFMOTD
            if "join" in data.connection.__conn_hooks__:
                key = data.connection.configuration.get_value('main', 'chan_key')
                data.connection.basic.join(
                    data.connection.configuration.get_value('main', 'channel'),
                    key = key if key is not None else None
                )
            if "pluginload" in data.connection.__conn_hooks__:
                data.connection.pluginloader.load()
        elif data.type.to_i() == 433:
            # ERR_NICKNAMEINUSE
            logging.getLogger('ashiema').error('<- %s, exiting.' % (data.message))
            data.connection.shutdown()
        return

class MessageEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler, "MessageEvent")
        self.__register__()
        self.commands = ['PRIVMSG']

    def match(self, data):
        if self.commands.__contains__(str(data.type)) and str(data.target) != data.connection.nick:
            return True
    
    def run(self, data):
        if self.callbacks is not None:
            for name, function in self.callbacks.iteritems():
                thread = get_thread(function, data)
                thread.setDaemon(True)
                thread.start()

class UserJoinedEvent(BasicUserEvent):

    def __init__(self, eventhandler):
        BasicUserEvent.__init__(self, eventhandler, "JoinEvent")
    
    def match(self, data):
        if str(data.type) == 'JOIN':
            return True
                
class UserPartedEvent(BasicUserEvent):

    def __init__(self, eventhandler):
        BasicUserEvent.__init__(self, eventhandler, "PartEvent")
    
    def match(self, data):
        if str(data.type) == 'PART':
            return True
    
class UserQuitEvent(BasicUserEvent):

    def __init__(self, eventhandler):
        BasicUserEvent.__init__(self, eventhandler, "QuitEvent")
       
    def match(self, data):
        if str(data.type) == 'QUIT':
            return True

class PingEvent(Event):
   
   def __init__(self, eventhandler):
       Event.__init__(self, eventhandler, "PingEvent")
       self.__register__()
   
   def match(self, data):
       if str(data.type) == 'PING':
           return True
   
   def run(self, data):
       if data.connection.debug: logging.getLogger('ashiema').debug('<- ping received at %s' % (time.time()))
       # form the response message
       resp = "PONG :%s" % (str(data.message))
       data.connection.send(resp)
       return