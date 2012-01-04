#!/usr/bin/env python

import Event, logging, time
from Event import Event

class DefaultEventChainloader(object):
    """ this chainloads all default events """
    
    def __init__(self, instance):
        RFCEvent(instance)
        MessageEvent(instance)
        PingEvent(instance)

    
class RFCEvent(Event):

    def __init__(self, instance):
        Event.__init__(self, instance)
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
        return

class MessageEvent(Event):

    def __init__(self, instance):
        Event.__init__(self, instance)
        self.__register__()
        self.commands = ['NOTICE', 'PRIVMSG']    

    def match(self, data):
        if self.commands.__contains__(str(data.type)):
            return True
    
    def run(self, data):
        return

class PingEvent(Event):
   
   def __init__(self, instance):
       Event.__init__(self, instance)
       self.__register__()
   
   def match(self, data):
       if str(data.type) == 'PING':
           return True
   
   def run(self, data):
       if self.connection.debug: logging.getLogger('ashiema').debug('<- ping received at %s' % (time.time()))
       # form the response message
       resp = "PONG :%s" % (str(data.message))
       self.connection.send(resp)
       return