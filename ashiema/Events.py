#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import logging, time, ashiema, datetime, sys, os
from ashiema.util import Configuration
import Connection, EventHandler, Structures
from ashiema.util.Configuration import Configuration
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

        self.logger = logging.getLogger('ashiema')

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

    def log_debug(self, *args):
        """ send data to the logger with level `debug`. """
        
        [self.logger.debug('[' + self.name + '] ' + message) for message in args]

    def log_info(self, *args):
        """ send data to the logger with level `info`. """
        
        [self.logger.info('[' + self.name + '] ' + message) for message in args]

    def log_warning(self, *args):
        """ send data to the logger with level `warning`. """
        
        [self.logger.warning('[' + self.name + '] ' + message) for message in args]

    def log_error(self, *args):
        """ send data to the logger with level `error`. """
        
        [self.logger.error('[' + self.name + '] ' + message) for message in args]

    def log_critical(self, *args):
        """ send data to the logger with level `critical`. """
        
        [self.logger.critical('[' + self.name + '] ' + message) for message in args]
    
    def match(self, data):
        """ this is a method that will provide the hooking system a mechanism
            to detect if a certain data value triggers a match on a registered
            event or not to help processing preservation. """
        
        pass

    def run(self, data):
        """ this provides a method to run when a line triggers an event.
            it must be overloaded. """
        
        pass


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

class IRCConnectionReadyEvent(Event):
    """ Represents completion of the bot's handshake with the server. """
    
    def __init__(self):
    
        Event.__init__(self, "IRCConnectionReadyEvent")
        self.__register__()
        
    def match(self, data = None):
    
        if str(data.target) == '*' and str(data.message).lstrip().startswith("***") and not data.connection._registered:
            return True
        else:
            return False
     
    def run(self, data = None):
     
        data.connection.send_registration()
        
        if self.callbacks is not None:
            for function in self.callbacks.values():
                function(data)

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
        # check if we should attempt to reconnect
        if Configuration.get_instance().get_section('main').get_bool('reconnect-on-err', True):
            self.log_info("======== Preparing to reconnect, stand by. ========")
            sys.argv.insert(0, "python")
            os.execvpe("python", sys.argv, os.environ)

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

class CAPEvent(Event):

    capabilities = []

    def __init__(self):
    
        Event.__init__(self, "CAPEvent")
        self.__register__()
        self.commands = ['CAP']
        
        self.connection = Connection.get_instance()
        self.config = Configuration.get_instance().get_section('main')
        self.extensions = self.config.get_list('capextensions')

    def match(self, data):
    
        if self.commands.__contains__(str(data.type)):
            return True

    def run(self, data):

        subcommand = data.message[0]
        arguments = data.message[1:]
        
        arguments[0] = arguments[0][1:]
        
        if len(self.extensions) == 0:
            self.log_info("No capabilities specified in configuration; skipping CAP negotiation.")
            self.connection.send("CAP END")

        if subcommand == 'LS':
            extensionlist = []
            for extension in self.extensions:
                if extension in arguments:
                    extensionlist.append(extension)
            self.connection.send("CAP REQ :%s" % (' '.join(extensionlist)))
        elif subcommand == 'ACK':
            for capability in arguments:
                CAPEvent.capabilities.append(capability)
            self.log_info("Registered capabilities: %s" % (','.join(CAPEvent.capabilities)))
            self.connection.send("CAP END")
        elif subcommand == 'NAK':
            self.log_error("Server refused extensions: %s" % (arguments))
            

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
        elif data.type.to_i() == 354:
            # RPL_WHOSPCRPL
            channel = Channel.get_channel(data.message[0])
            if channel is None:
                pass
            channel.parse_who(data)
        elif data.type.to_i() == 376 or data.type.to_i() == 422:
            # RPL_ENDOFMOTD or ERR_NOMOTD
            if "join" in self.__conn_hooks__:
                channel = self.config.get_string('channel', None)
                key = self.config.get_string('chan_key', None)
                self.connection.send(Channel.join(channel, key))
            if "pluginload" in self.__conn_hooks__:
                PluginLoader.get_instance().load()
        elif data.type.to_i() == 433:
            # ERR_NICKNAMEINUSE # XXX - Quit just exiting. Implement a nick change/tracking mechanism.
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

class UserJoinEvent(Event):

    def __init__(self):

        Event.__init__(self, "UserJoinEvent")
        self.__register__()
    
    def match(self, data):

        if str(data.type) == 'JOIN':
            return True
        else:
            return False

    def run(self, data):
    
        self.log_debug("<- user %s joined channel %s" % (data.origin.to_s(), data.message.to_s()))

class UserPartEvent(Event):

    def __init__(self):

        Event.__init__(self, "UserPartEvent")
        self.__register__()
    
    def match(self, data):

        if str(data.type) == 'PART':
            return True
        else:
            return False
    
    def run(self, data):
    
        if not data.target:    
            self.log_debug("<- user %s parted channel %s" % (data.origin.to_s(), data.message.to_s()))
        else:
            self.log_debug("<- user %s parted channel %s: %s" % (data.origin.to_s(), data.target.to_s(), data.message.to_s()))

class UserQuitEvent(Event):

    def __init__(self):

        Event.__init__(self, "UserQuitEvent")
       
    def match(self, data):

        if str(data.type) == 'QUIT':
            return True
        else:
            return False

    def run(self, data):
    
        self.log_debug("<- user %s has quit: %s" % (data.origin.to_s(), data.message.to_s()))

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
            data.origin.notice("VERSION ashiema IRC bot [%s] - http://github.com/pirogoeth/ashiema" % (ashiema.version))
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

    return { 'RFCEvent'                     : RFCEvent(), # mainly server triggered events
             'CAPEvent'                     : CAPEvent(),
             'PingEvent'                    : PingEvent(),
             'ErrorEvent'                   : ErrorEvent(),
             'ModeChangeEvent'              : ModeChangeEvent(),
             'CTCPEvent'                    : CTCPEvent(),
             'IRCConnectionReadyEvent'      : IRCConnectionReadyEvent(),
             'MessageEvent'                 : MessageEvent(), # user triggered events
             'PMEvent'                      : PMEvent(),
             'JoinEvent'                    : UserJoinEvent(),
             'PartEvent'                    : UserPartEvent(),
             'QuitEvent'                    : UserQuitEvent(),
             'PluginsLoadedEvent'           : PluginsLoadedEvent() # system triggered events
           }