#!/usr/bin/env python

import Event, logging, time, threading
from Event import Event

get_thread = lambda func, data: threading.Thread(target = func, args = (data,))

class DefaultEventChainloader(object):
    """ this chainloads all default events """
    
    def __init__(self, eventhandler):
        self.defaults = {
            'RFCEvent': RFCEvent(eventhandler),
            'MessageEvent': MessageEvent(eventhandler),
            'PingEvent': PingEvent(eventhandler)
        }
    
    def get_events(self):
        return self.defaults
    
    def get_count(self):
        return len(self.defaults)

    
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
        elif data.type.to_i() == 376:
            # RPL_ENDOFMOTD
            if "onjoin" in data.connection.__conn_hooks__:
                data.connection.basic.join(
                    data.connection.configuration.get_value('main', 'channel'),
                    data.connection.configuration.get_value('main', 'chan_key')
                )
        return

class MessageEvent(Event):

    def __init__(self, eventhandler):
        Event.__init__(self, eventhandler)
        self.__register__()
        self.commands = ['NOTICE', 'PRIVMSG']    
        self.callbacks = []
       
    def register(self):
        """ registers a function to be run on the processed data. """
        def wrapper(function):
            def new(*args, **kw):
                self.callbacks.append(function)
            return new
        return wrapper

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