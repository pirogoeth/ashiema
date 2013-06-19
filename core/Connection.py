#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import socket, select, ssl, logging, time, signal, sys, collections, pprint
import Logger, Tokenizer
from util import Configuration, apscheduler
from util.apscheduler import scheduler
from util.apscheduler.scheduler import Scheduler
from util.Configuration import Configuration
from Tokenizer import Tokenizer

class Connection(object):
    """ Connection object to manage the connection 
        to the uplink """
        
    __instance = None

    @staticmethod
    def get_instance():
        
        if Connection.__instance is None:
            return Connection()
        else:
            return Connection.__instance

    def __init__(self):
        """ initialise connection object. """

        Connection.__instance = self
    
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._setupdone, self._connected, self._registered, self._passrequired, self.debug = (False, False, False, False, False)
        self.log = logging.getLogger('ashiema')
        self._queue = collections.deque()
        self._scheduler = Scheduler()
        self.tasks = {}
   
    """ information setup """
    def setup_info(self, nick = '', ident = '', real = ''):
        """ set up post connection info. """
        
        self.nick = nick
        self.ident = ident
        self.real = real
        self._setupdone = True
    
        return self

    def set_debug(self, debug = True):
        """ set connection debug logging. """
        
        self.debug = debug
        
        return self
    
    """ flag management """
    def shutdown(self):
        """ change the self._connection flag to shut down the bot """
        
        # shut down the scheduler
        self._scheduler.shutdown()
        # change the value that controls the connection loop
        self._connected = False
        
    """ socket manipulation and management """
    def connect(self, address = '', port = '', _ssl = None, password = None):
        """ complete the connection process. """

        assert self._setupdone is True, 'Information setup has not been completed.'
        assert address and port, 'Parameters for connection have not been provided.'
        
        _ssl = True if _ssl == True or _ssl == "True" or _ssl == "true" else False
        if _ssl is True:
            self.connection = ssl.wrap_socket(self._socket)
            self.log.info("Connection type: SSL")
        elif _ssl is False:
            self.connection = self._socket
            self.log.info("Connection type: Plain")
        else:
            self.connection = self._socket
            self.log.warning("Connection type not specified, assuming plain.")
        if password is not None or password is not '':
            self._passrequired, self._password = (True, password)
        self.connection.connect((address, int(port)))
        # we're connected!
        self._connected = True
        
        return self
    
    def send(self, data):
        """ function to add a line to the sendqueue to be sent. """
        
        assert self._setupdone is True, 'Information setup has not been completed.'
        assert self._connected is True, 'Connection to the uplink has not yet been established.'

        data = data.decode('UTF-8', 'ignore')
        self._queue.append(data.encode("UTF-8") + '\r\n')
    
    def _raw_send(self, data):
        """ allows sending of raw data directly to the uplink 
            assumes +data+ has received all necessary formatting to actually be read and processed by the uplink """
        
        assert self._setupdone is True, 'Information setup has not been completed.'
        assert self._connected is True, 'Connection to the uplink has not yet been established.'

        if not data.endswith('\r\n'):
            data = data + '\r\n'

        self.connection.send(data)
    
    def get_scheduler(self):
        """ returns the scheduler instance. """
        
        return self._scheduler
   
    def run(self):
        """ runs the polling loop. 
            this should run off of two assertions:
            self._connected is true, and self._setupdone is true."""
        
        assert self._setupdone is True, 'Information setup has not been completed.'
        assert self._connected is True, 'Connection to the uplink has not yet been established.'
        
        # start the scheduler
        self._scheduler.start()
        # cycle counter
        _cc = 1
        while self._connected is True:
            try:
                # first, sleep so we don't slurp up CPU time like no tomorrow
                time.sleep(0.001)
                # send user registration if we're not already registered and about 20 cycles have passed
                if not self._registered and _cc is 20:
                    if self._passrequired: 
                        self.send("PASS :%s" % (self._password))
                        self._password = None
                    self.send("NICK %s" % (self.nick))
                    self.send("USER %s +iw %s :%s" % (self.nick, self.ident, self.real))
                    self._registered = True
                # now, select.
                r, w, e = select.select([self.connection], [], [self.connection], .025)
                # now GO!
                if self.connection in r:
                    self.parse(self.connection.recv(35000))
                # check if im in the errors
                if self.connection in e:
                    self._connected = False
                    self.log.critical("Error during poll; aborting!")
                    break
                # process the data thats in the queue
                try:
                    [self._raw_send(data) for data in [self._queue.popleft() for count in xrange(0, 1)]]
                except (AssertionError, IndexError) as e:
                    pass
                except (KeyboardInterrupt, SystemExit) as e:
                    self.shutdown()
                    raise
                _cc += 1
            except (KeyboardInterrupt, SystemExit) as e:
                self.shutdown()
                raise
        # what are we going to do after the loop closes?
        self.log.info("Shutting down.")
        self.connection.close()
        self._socket.close()
        exit()
    
    """ data parsing and event dispatch """
    def parse(self, data):
        
        assert self._connected is True, 'Connection to the uplink has not yet been established.'
        
        data = data.split('\r\n')
        for line in data:
             # serialisation.
             line = Tokenizer(line)
             # fire off all events that match the data.
             Tokenizer.process_events(line)