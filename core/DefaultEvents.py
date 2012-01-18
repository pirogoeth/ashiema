#!/usr/bin/env python

import Event, logging, time, threading, core
from Event import Event
from core import get_connection

get_thread = lambda func, data: threading.Thread(target = func, args = (data,))

class DefaultEventChainloader(object):
    """ this chainloads all default events """
    
    def __init__(self, eventhandler):
        self.defaults = {
            'RFCEvent': RFCEvent(eventhandler),
            'MessageEvent': MessageEvent(eventhandler),
            'PMEvent': PMEvent(eventhandler),
            'PingEvent': PingEvent(eventhandler),
            'ErrorEvent': ErrorEvent(eventhandler),
            'PluginsLoadedEvent': PluginsLoadedEvent(eventhandler)
        }
    
    def get_events(self):
        return self.defaults
    
    def get_count(self):
        return len(self.defaults)

class PluginsLoadedEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler)
        self.__register__()
        self.callbacks = {}
    
    def register(self, function):
        self.callbacks.update(
        {
            function.__name__ : function
        })
    
    def deregister(self, function):
        del self.callbacks[function.__name__]
        
    def callback(self):
        """ registers a function to be run on the processed data. """
        def wrapper(function):
            def new(*args, **kw):
                self.callbacks.update(
                {
                    function.__name__ : function
                })
            return new
        return wrapper

    def match(self, data = None):
        return get_connection().pluginloader._loaded
    
    def run(self, data = None):
        for name, eventhandler in self.callbacks.iteritems():
            eventhandler()

class ErrorEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler)
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
        Event.__init__(self, eventhandler)
        self.__register__()
        self.commands = ['PRIVMSG']
        self.callbacks = []
       
    def callback(self):
        """ registers a function to be run on the processed data. """
        def wrapper(function):
            def new(*args, **kw):
                self.callbacks.append(function)
            return new
        return wrapper

    def register(self, function):
        self.callbacks.append(function)

    def deregister(self, function):
        self.callbacks.remove(function)

    def match(self, data):
        if self.commands.__contains__(str(data.type)) and data.target == data.connection.nick:
            return True

    def run(self, data):
        if self.callbacks is not None:
            for function in self.callbacks:
                thread = get_thread(function, data)
                thread.setDaemon(True)
                thread.start()

class RFCEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler)
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
        elif data.type.to_i() == 433:
            # ERR_NICKNAMEINUSE
            logging.getLogger('ashiema').error('<- %s, exiting.' % (data.message))
            data.connection.shutdown()
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
        return

class MessageEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler)
        self.__register__()
        self.commands = ['NOTICE', 'PRIVMSG']
        self.callbacks = []
       
    def callback(self):
        """ registers a function to be run on the processed data. """
        def wrapper(function):
            def new(*args, **kw):
                self.callbacks.append(function)
            return new
        return wrapper

    def register(self, function):
        self.callbacks.append(function)

    def deregister(self, function):
        self.callbacks.remove(function)

    def match(self, data):
        if self.commands.__contains__(str(data.type)):
            return True
    
    def run(self, data):
        if self.callbacks is not None:
            for function in self.callbacks:
                thread = get_thread(function, data)
                thread.setDaemon(True)
                thread.start()

class PingEvent(Event):
   
   def __init__(self, eventhandler):
       Event.__init__(self, eventhandler)
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