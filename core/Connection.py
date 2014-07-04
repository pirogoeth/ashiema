#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import socket, select, ssl, logging, time, signal, sys, collections, multiprocessing, re, logging, traceback
import Logger, EventHandler, Structures, PluginLoader
from PluginLoader import PluginLoader
from util import Configuration, apscheduler
from util.apscheduler import scheduler
from util.apscheduler.scheduler import Scheduler
from util.Configuration import Configuration

""" module:: Connection
    :platform: Unix, Windows, Mac OS X
    :synopsis: Contains Connection and Tokener (line tokenizing) classes. """

class Connection(object):
    """ py:class:: Connection()

        Manage the connection to a server and run the main parsing/event loop. """

    __instance = None

    @staticmethod
    def get_instance():
        """ py:staticmethod:: get_instance()
            
            :returns: The Connection instance, if it exists, or a new Connection instance.
            :rtype: Connection """

        if Connection.__instance is None:
            return Connection()
        else:
            return Connection.__instance

    def __init__(self):
        """ py:function:: __init__(self)
        
            Sets up the socket, send queue, communications pipe, and scheduler. """

        Connection.__instance = self
    
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._setupdone, self._connected, self._registered, self._passrequired, self.debug = (False, False, False, False, False)
        self.log = logging.getLogger('ashiema')
        self._queue = collections.deque()
        self._pqueue, self.__pq_reasm = collections.deque(), None
        self._comm_pipe_recv, self._comm_pipe_send = multiprocessing.Pipe(False)
        self._scheduler = Scheduler()
        self.tasks = {}
   
    def setup_info(self, nick = '', ident = '', real = ''):
        """ py:function:: setup_info(self[, nick = ''[, ident = ''[, real = '']]])
        
            Sets up the data that is necessary for connecting to a server.
        
            :param nick: The nickname to connect with.
            :type nick: str
            :param ident: The ident string to connect with.
            :type ident: str
            :param real: The real name to connect with.
            :type real: str
            :returns: current Connection instance for chaining.
            :rtype: Connection """
        
        self.nick = nick
        self.ident = ident
        self.real = real
        self._setupdone = True
    
        return self

    def set_debug(self, debug = True):
        """ py:function:: set_debug(self[, debug = True])

            Sets the flag for whether or not we will show debugging output.

            :param debug: Whether or not to show debug output.
            :type debug: bool
            :returns: current Connection instance for chaining.
            :rtype: Connection """
        
        self.debug = debug
        
        return self
    
    def shutdown(self):
        """ py:function:: shutdown(self)

            Shuts down the scheduler and terminates the parsing/event loop. """
        
        # shut down the scheduler
        self._scheduler.shutdown()
        # unload plugins
        PluginLoader.get_instance().unload()
        # change the value that controls the connection loop
        self._connected = False
        
    def connect(self, address = '', port = '', _ssl = None, password = None):
        """ py:function:: connect(self[, address = ''[, port = ''[, _ssl = None[, password = None]]]])

            Checks if the connection socket should be ssl wrapped and wraps it if so, and connects
            the socket to the target server.
            
            :param address: Address of the server to connect to.
            :type address: str
            :param port: Port to connect to on the specified server.
            :type port: str
            :param _ssl: Whether or not the socket should be SSL wrapped.
            :type _ssl: bool
            :param password: Password to use to connect to the server, if any.
            :type password: str
            :returns: current Connection instance for chaining.
            :rtype: Connection """
            

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
        try: self.connection.connect((address, int(port)))
        except: raise
        self._connected = True
        
        return self
    
    def send_registration(self):
        """ py:function:: send_registration(self)

            Sends registration commands in the following order.
        
              PASS :<password> (if a password is set/provided)
              NICK <nick>
              CAP LS
              USER <nick> +iw <unused> :<realname>
            
            Sends the password and registration information to the server. """

        if not self._connected: return
        if self._registered: return

        if not self._registered:  # we probably don't need this any longer...
            if self._passrequired: 
                self.send("PASS :%s" % (self._password))
                self._password = None
            self.send("NICK %s" % (self.nick))
            self.send("CAP LS")
            self.send("USER %s %s %s :%s" % (self.nick, self.nick, self.ident, self.real))
            self._registered = True
    
    def send(self, *lines):
        """ py:function:: send(self, *lines)
            
            Encodes given data in UTF-8 format, then adds it to the send queue.
            
            :param lines: Lines that should be appended to the send queue.
            :type lines: list of strings """
        
        if not self._connected: return

        for line in lines:
            try: line = line.encode("utf-8", "ignore")
            except: pass
            self._queue.append(line + '\r\n')
    
    def _raw_send(self, data, override = False):
        """ py:function:: _raw_send(self, data)
        
            Verifies data has the proper line ending and sends it through the socket.
            
            :param data: Data to send to the server.
            :type data: str """
        
        if not self._connected: return

        if data.strip() == '' and not override:
            return

        if not data.endswith('\r\n'):
            data = data + '\r\n'

        self.connection.send(data)
    
    def get_scheduler(self):
        """ py:function:: get_scheduler(self)
            
            Returns the scheduler instance.
            
            :returns: Current scheduler instance. 
            :rtype: Scheduler """
        
        return self._scheduler
    
    def get_send_pipe(self):
        """ py:function:: get_send_pipe(self)
        
            Returns the sending side of the multiprocessing.Pipe connection for subprocesses.
            
            :returns: Sending side of the multiprocessing.Pipe connection.
            :rtype: multiprocessing.Connection """
        
        return self._comm_pipe_send
   
    def run(self):
        """ py:function:: run(self)
            
            Runs the parsing/event loop.
            
            Handles the first message off the top of the send queue and handles what ever data is waiting
            in the subprocess pipe. """
        
        if not self._connected: return
        
        # start the scheduler
        self._scheduler.start()
        while self._connected is True:
            try:
                time.sleep(0.001)
                r, w, e = select.select([self.connection], [], [self.connection], .025)
                if self.connection in r:
                    self.parse(self.connection.recv(8192))
                if self.connection in e:
                    self._connected = False
                    self.log.critical("Error during poll; aborting!")
                    break
                if not self._registered:
                    self._raw_send('\r\n', override = True)
                # process data that is currently in the sending queue.
                try:
                    [self._raw_send(data) for data in [self._queue.popleft() for count in xrange(0, 1)]]
                except (AssertionError, IndexError) as e: pass
                except (KeyboardInterrupt, SystemExit) as e:
                    self.shutdown()
                    raise
                # process data that is waiting in the subprocess pipe.
                try:
                    if self._comm_pipe_recv.poll(.025):
                        self.send(self._comm_pipe_recv.recv())
                except (EOFError, IOError): pass
                except (KeyboardInterrupt, SystemExit) as e:
                    self.shutdown()
                    raise
            except (AssertionError) as e: pass
            except (KeyboardInterrupt, SystemExit) as e:
                self.shutdown()
                raise
        self.log.info("Shutting down.")
        self.connection.close()
        self._socket.close()
        exit()
    
    def parse(self, data):
        """ py:function:: parse(self, data)

            Processes a chunk of data by splitting the chunk at each '\r\n', then tokenizes each line, and
            processes each token.
            
            :param data: Chunk of data to be parsed.
            :type data: str """
        
        self._pqueue.extend(data.split('\r\n'))
        
        _reasm = None
        
        if self.__pq_reasm:
            _reasm = self.__pq_reasm
            self.__pq_reasm = None
        
        if not data.endswith('\r\n'):
            self.__pq_reasm = self._pqueue[len(self._pqueue) - 1]
        
        while (len(self._pqueue) > 0):
            line = self._pqueue.popleft()
            if self.__pq_reasm and len(self._pqueue) == 0:
                break
            if _reasm:
                line = _reasm + line
                _reasm = None
            line = Tokener(line)
            Tokener.process_events(line)
        
class Tokener(object):
    """ py:class:: Tokener(data)
    
        Uses a regex to split up a line and turn each matched group (Origin, Type, Target, Message)
        into a Structure that makes usage, responding, and formatting much easier. """

    @staticmethod
    def process_events(data):
        """ py:staticmethod:: process_events(data)
            
            Passes +data+ to the EventHandler's event mapper for processing.
            
            :param data: Line to be processed.
            :type data: Tokener instance """
        
        EventHandler.EventHandler.get_instance().map_events(data)

    def __init__(self, data):
        """ py:function:: __init__(self, data)
            
            Tokenizes +data+ according to a regex and matches each group with the proper Structure based on content.
            
            :param data: Data to tokenize.
            :type data: str """

        self._raw = data
        self.connection = Connection.get_instance()
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
            # print self.origin, "|", self.type, "|", self.target, "|", self.message # debug
        except (AttributeError):
            pass
            # print "Could Not Parse Message:", self._raw # debug
        try:
            if logging.getLogger('ashiema').getEffectiveLevel() is logging.DEBUG and self.connection.debug is True:
                if self.type and self.message:
                    logging.getLogger('ashiema').debug("%s %s %s %s" % (str(self.origin), str(self.type), str(self.target), str(self.message)))
        except:
            [logging.getLogger('ashiema').error(trace) for trace in traceback.format_exc(5).split('\n')]
            pass
    
    def get_raw(self):
        """ py:function:: get_raw(self)
            
            Returns the raw, untokenized data that was received from the server.
            
            :returns: Untokenized data.
            :rtype: str """

        return self._raw
    
    def respond_to_user(self, message, prefer_notice = True):
        """ py:function:: respond_to_user(self, message[, prefer_notice = True])
        
            Determines the best way to respond to the user and sends +message+ that way.
            If +prefer_notice+ is true, the message will be sent as a NOTICE instead of a 
            PRIVMSG.
            
            :param message: Message to send to the user.
            :type message: str
            :param prefer_notice: Whether to use NOTICE or PRIVMSG.
            :type prefer_notice: bool """

        if self.target.is_self():
            if prefer_notice:
                self.origin.notice(message)
            else:
                self.origin.message(message)
        else:
            self.target.message(message)