#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import logging, time, core, datetime, sys
from core.util import Configuration
import Connection, EventHandler, Structures
from core.util.Configuration import Configuration
from Connection import Connection
from EventHandler import EventHandler
from PluginLoader import PluginLoader
from Structures import Channel

class Event(object):
    """ This is the base event class that should be subclassed by all other events
        that are being implemented. We provide a small framework to easily handle
        registration and deregistration of handlers. """
    
    def __init__(self, event_name = "Event"):

        self.eventhandler = EventHandler.get_instance()
        self.connection = Connection.get_instance()

        self.name = event_name
        self.callbacks = {}

        self.get_method_ident = lambda func: str(func.__module__) + str(func.__name__)
        
    def __repr__(self):

        return "<Event(%s)>" % (type(self).__name__)

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


class BasicUserEvent(Event):
    """ This event represents a user action, such as joining a channel, parting
        a channel, or quitting from the IRC network. The events that subclass this
        will each provide their own method of detecting what the user action was. """

    def __init__(self, event_name = "BasicUserEvent"):

        Event.__init__(self, event_name = "BasicUserEvent")
        self.__register__()
    
    def match(self, data):

        pass
    
    def run(self, data):

        if self.callbacks is not None:
            for function in self.callbacks.values():
                function(data)

class PluginsLoadedEvent(Event):
    """ This event represents the completion of the plugin load cycle in the PluginLoader. """

    def __init__(self):

        Event.__init__(self, "PluginsLoadedEvent")
        self.__register__()

    def match(self, data = None):

        if isinstance(data, tuple) and PluginLoader.get_instance()._loaded:
            return True
        else:
            return False
    
    def run(self, data = None):

        for callback in self.callbacks.values():
            callback()

class ModeChangeEvent(Event):

    def __init__(self):

        Event.__init__(self, "ModeChangeEvent")
        self.__register__()
        self.commands = ['MODE', 'OMODE', 'UMODE']
    
    def match(self, data = None):

        if self.commands.__contains__(str(data.type)) and data.target == data.connection.nick:
            return True
        else:
            return False
    
    def run(self, data):

        if self.callbacks is not None:
            for function in self.callbacks.values():
                function(data)

class ErrorEvent(Event):

    def __init__(self):

        Event.__init__(self, "ErrorEvent")
        self.__register__()
    
    def match(self, data):

        if (str(data.type) == "ERROR" or str(data.type) == "KILL") and data.message:
            return True
        else:
            return False
    
    def run(self, data):

        logging.getLogger('ashiema').critical('<- %s: %s' % (str(data.type), data.message))
        # adjust the loop shutdown flag
        data.connection.shutdown()

class PMEvent(Event):

    def __init__(self):

        Event.__init__(self, "PMEvent")
        self.__register__()
        self.commands = ['PRIVMSG']

    def match(self, data):

        if self.commands.__contains__(str(data.type)) and str(data.target) == data.connection.nick:
            return True
        else:
            return False

    def run(self, data):

        if self.callbacks is not None:
            for function in self.callbacks.values():
                function(data)

class RFCEvent(Event):

    def __init__(self):

        Event.__init__(self, "RFCEvent")
        self.__register__()
        
        self.connection = Connection.get_instance()
        self.config = Configuration.get_instance().get_section('main')
        self.__conn_hooks__ = self.config.get_string('onconnect', '').split(',')
    
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
            # RPL_NAMEREPLY
            pass
        elif data.type.to_i() == 376:
            # RPL_ENDOFMOTD
            if "join" in self.__conn_hooks__:
                channel = self.config.get_string('channel', None)
                key = self.config.get_string('chan_key', None)
                self.connection.send(Channel.join(channel, key))
            if "pluginload" in self.__conn_hooks__:
                PluginLoader.get_instance().load()
        elif data.type.to_i() == 433:
            # ERR_NICKNAMEINUSE
            logging.getLogger('ashiema').error('<- %s, exiting.' % (data.message))
            self.connection.shutdown()
        
        if self.callbacks is not None:
            for function in self.callbacks.values():
                function(data)

class MessageEvent(Event):

    def __init__(self):

        Event.__init__(self, "MessageEvent")
        self.__register__()
        self.commands = ['PRIVMSG']

    def match(self, data):

        if self.commands.__contains__(str(data.type)) and str(data.target) != data.connection.nick:
            return True
    
    def run(self, data):

        if self.callbacks is not None:
            for name, function in self.callbacks.iteritems():
                function(data)

class UserJoinedEvent(BasicUserEvent):

    def __init__(self):

        BasicUserEvent.__init__(self, "JoinEvent")
    
    def match(self, data):

        if str(data.type) == 'JOIN':
            return True
        else:
            return False
                
class UserPartedEvent(BasicUserEvent):

    def __init__(self):

        BasicUserEvent.__init__(self, "PartEvent")
    
    def match(self, data):

        if str(data.type) == 'PART':
            return True
        else:
            return False
    
class UserQuitEvent(BasicUserEvent):

    def __init__(self):

        BasicUserEvent.__init__(self, "QuitEvent")
       
    def match(self, data):

        if str(data.type) == 'QUIT':
            return True
        else:
            return False

class PingEvent(Event):
   
    def __init__(self):

        Event.__init__(self, "PingEvent")
        self.__register__()
   
    def match(self, data):

        if str(data.type) == 'PING':
            return True
        else:
            return False
   
    def run(self, data):

        if data.message is None:
            data.message = data._raw.split(":")[1]
        if data.connection.debug: logging.getLogger('ashiema').debug('<- ping received at %s, has data "%s"' % (time.time(), str(data.message)))
        # form the response message
        resp = "PONG :%s" % (str(data.message))
        data.connection.send(resp)
        return

class CTCPEvent(Event):

    def __init__(self):

        Event.__init__(self, "CTCPEvent")
        self.__register__()
        
    def match(self, data):

        if str(data.type) == 'PRIVMSG' and data.target.is_self():
            if data.message == (0, "\x01VERSION\x01"):
                return True
            elif data.message == (0, "\x01TIME\x01"):
                return True
            elif data.message == (0, "\x01PING\x01"):
                return True
            elif data.message == (0, "\x01DCC\x01"):
                return True
            else:
                return False

    def run(self, data):

        if data.message == (0, "\x01VERSION\x01"):
            data.origin.notice("VERSION ashiema IRC bot [%s] - http://github.com/pirogoeth/ashiema" % (core.version))
        elif data.message == (0, "\x01TIME\x01"):
            data.origin.notice("TIME %s" % (datetime.datetime.now().strftime("%a %d %b %Y %I:%M:%S %p %Z")))
        elif data.message == (0, "\x01PING\x01"):
            try: resp = data.message[1]
            except: resp = "Pong!"
            data.origin.notice("PING %s" % (resp))
        elif data.message == (0, "\x01DCC\x01"):
            data.origin.notice("DCC Not Available")
        else:
            return

def get_events():

    return { 'RFCEvent'          : RFCEvent(), # mainly server triggered events
             'PingEvent'         : PingEvent(),
             'ErrorEvent'        : ErrorEvent(),
             'ModeChangeEvent'   : ModeChangeEvent(),
             'CTCPEvent'         : CTCPEvent(),
             'MessageEvent'      : MessageEvent(), # user triggered events
             'PMEvent'           : PMEvent(),
             'JoinEvent'         : UserJoinedEvent(),
             'PartEvent'         : UserPartedEvent(),
             'QuitEvent'         : UserQuitEvent(),
             'PluginsLoadedEvent': PluginsLoadedEvent() # system triggered events
           }