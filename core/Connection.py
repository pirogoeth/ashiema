#!/usr/bin/env python

import socket, select, ssl, logging, time
import Queue, Logger, Serialise
from Queue import Queue, QueueError
from Serialise import Serialise

class Connection(object):
    """ Connection object to manage the connection 
        to the uplink """
    
    def __init__(self):
        """ initialise connection object. """
    
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._setupdone, self._connected, self._registered, self._passrequired, self.debug = (False, False, False, False, False)
        self.log = logging.getLogger('ashiema')
        self._queue = Queue()

    """ information setup """
    def setup_info(self, nick, ident, real):
        """ set up post connection info. """
        
        self.nick = nick
        self.ident = ident
        self.real = real
        self._setupdone = True
    
    def set_debug(self, debug):
        """ set logger debugging. """
        
        self.debug = debug
        Logger.set_debug(debug)
    
    """ socket manipulation and management """
    def connect(self, address, port, _ssl = None, password = None):
        """ complete the connection process. """

        assert self._setupdone is True, 'Information setup has not been completed.'
        
        _ssl = True if _ssl is True or _ssl is "True" or _ssl is "true" else False
        if _ssl is True:
            self.connection = ssl.wrap_socket(self._socket)
            self.log.info("connection type: SSL")
        elif _ssl is False:
            self.connection = self._socket.makefile()
            self.log.info("connection type: plain")
        else:
            self.connection = self._socket.makefile()
            self.log.warning("connection type not specified, assuming plain.")
        if password is not None:
            self._passrequired, self._password = (True, password)
        self.connection.connect((address, port))
        # we're connected!
        self._connected = True
    
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

        if self.debug: print data
        self.connection.send(data)
   
    def run(self):
        """ runs the polling loop. 
            this should run off of two assertions:
            self._connected is true, and self._setupdone is true."""
        
        assert self._setupdone is True, 'Information setup has not been completed.'
        assert self._connected is True, 'Connection to the uplink has not yet been established.'
        
        # cycle counter
        _cc = 1
        while self._connected is True:
            # first, sleep so we don't slurp up CPU time like no tomorrow
            time.sleep(0.005)
            # send user registration if we're not already registered and about 35 cycles have passed
            if not self._registered and _cc is 10:
                # remove this line
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
                self.parse(self.connection.recv(31337))
            # check if im in the errors
            if self.connection in e:
                self._connected = False
                self.log.severe("error during poll; aborting")
                break
            # process the data thats in the queue
            try:
                [self._raw_send(data) for data in [self._queue.pop() for count in xrange(0, 1)]]
            except (QueueError), e:
                self.log.warning("{QueueError}: %s" % (e))
                pass
            _cc += 1
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
             line = Serialise(line)
             line.print_raw()