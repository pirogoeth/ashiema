#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import socket, select, ssl, logging, time, signal
import Queue, Logger, Serialise, EventHandler, BasicFunctions, PluginLoader
from util import apscheduler
from util.apscheduler import scheduler
from util.apscheduler.scheduler import Scheduler
from PluginLoader import PluginLoader
from BasicFunctions import Basic
from Queue import Queue, QueueError
from Serialise import Serialise
from EventHandler import EventHandler

class Connection(object):
    """ Connection object to manage the connection 
        to the uplink """
        
    def __init__(self, configuration):
        global connection
        """ initialise connection object. """
    
        self.configuration = configuration
        self.__conn_hooks__ = configuration.get_value('main', 'onconnect').split(',')
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._setupdone, self._connected, self._registered, self._passrequired, self.debug = (False, False, False, False, False)
        self.log = logging.getLogger('ashiema')
        self.basic = Basic(self)
        self._queue = Queue()
        self._evh = EventHandler()
        self.pluginloader = PluginLoader((self, self._evh))
        self.scheduler = Scheduler()
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
        
        # unload all plugins
        self.pluginloader.unload()
        # shut down all leftover apscheduler tasks
        for task in self.tasks:
            self.scheduler.unschedule_job(task)
        # shut down the scheduler
        self.scheduler.shutdown()
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
            self.log.info("connection type: SSL")
        elif _ssl is False:
            self.connection = self._socket
            self.log.info("connection type: plain")
        else:
            self.connection = self._socket
            self.log.warning("connection type not specified, assuming plain.")
        if password is not None:
            self._passrequired, self._password = (True, password)
        self._evh.load_default_events()
        self.connection.connect((address, int(port)))
        # we're connected!
        self._connected = True
        
        return self
    
    def send(self, data):
        """ function to add a line to the sendqueue to be sent. """
        
        assert self._setupdone is True, 'Information setup has not been completed.'
        assert self._connected is True, 'Connection to the uplink has not yet been established.'

        self._queue.append(data + '\r\n')
    
    def _raw_send(self, data):
        """ allows sending of raw data directly to the uplink 
            assumes +data+ has received all necessary formatting to actually be read and processed by the uplink """
        
        assert self._setupdone is True, 'Information setup has not been completed.'
        assert self._connected is True, 'Connection to the uplink has not yet been established.'

        self.connection.send(data.encode('UTF-8'))
   
    def run(self):
        """ runs the polling loop. 
            this should run off of two assertions:
            self._connected is true, and self._setupdone is true."""
        
        assert self._setupdone is True, 'Information setup has not been completed.'
        assert self._connected is True, 'Connection to the uplink has not yet been established.'
        
        # start the scheduler
        self.scheduler.start()
        # cycle counter
        _cc = 1
        while self._connected is True:
            try:
                # first, sleep so we don't slurp up CPU time like no tomorrow
                time.sleep(0.005)
                # send user registration if we're not already registered and about 35 cycles have passed
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
                    self.log.severe("error during poll; aborting")
                    break
                # process the data thats in the queue
                try:
                    [self._raw_send(data) for data in [self._queue.pop() for count in xrange(0, 1)]]
                except (QueueError):
                    pass
                _cc += 1
            except (KeyboardInterrupt, SystemExit) as e:
                self.shutdown()
        # what are we going to do after the loop closes?
        self.log.info("shutting down.")
        self.connection.close()
        self._socket.close()
        exit()
    
    """ data parsing and event dispatch """
    def parse(self, data):
        
        assert self._connected is True, 'Connection to the uplink has not yet been established.'
        
        data = data.split('\r\n')
        for line in data:
             # serialisation.
             line = Serialise(line, (self, self._evh))
             # fire off all events that match the data.
             self._evh.map_events(line)