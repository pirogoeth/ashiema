# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013-2015 Sean Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import ashiema, collections, inspect, malibu, multiprocessing, select, signal
import socket, ssl, sys, time, traceback

from ashiema.irc import structures
from ashiema.irc.eventhandler import EventHandler
from ashiema.irc.token import Token
from ashiema.plugin.loader import PluginLoader
from ashiema.util import get_caller

from malibu.config.configuration import Configuration
from malibu.util.log import LoggingDriver
from malibu.util.scheduler import Scheduler


class Connection(object):
    """ Manage the connection to a server and run the main parsing/event loop.
    """

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

        self.log = LoggingDriver.find_logger()
        # Fields used for upstream processing.
        self._socket = None
        self._queue = collections.deque()
        self._pqueue = collections.deque()
        self.__pq_reasm = None
        # Fields for tracking connection state.
        self._setupdone = False
        self._connected = False
        self._registered = False
        self._passrequired = False
        self.debug = False
        # Inter-process plugin communication pipe
        self._comm_pipe_recv, self._comm_pipe_send = multiprocessing.Pipe(False)
        # Scheduler, event ticker
        self._scheduler = Scheduler()

    def setup_info(self, nick, ident, real = ''):
        """ py:function:: setup_info(self[, nick[, ident[, real = '']]])

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

            Deinitializes plugins and terminates the parsing/event loop. """

        # unload plugins
        PluginLoader.get_instance().unload()
        # change the value that controls the connection loop
        self._connected = False

    def connect(self, address = '', inettype = 4, port = '', _ssl = None, password = None):
        """ py:function:: connect(self[, address = ''[, port = ''[, _ssl = None[, password = None]]]])

            Checks if the connection socket should be ssl wrapped and wraps it if so, and connects
            the socket to the target server.

            :param address: Address of the server to connect to.
            :type address: str
            :param inettype: Inet socket type.
            :type inettype: int
            :param port: Port to connect to on the specified server.
            :type port: str
            :param _ssl: Whether or not the socket should be SSL wrapped.
            :type _ssl: bool
            :param password: Password to use to connect to the server, if any.
            :type password: str
            :returns: current Connection instance for chaining.
            :rtype: Connection """

        if inettype == 4:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif inettype == 6:
            self._socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            address = address[1:-1]
        else:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
            self._passrequired = True
            self._password = password

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
            self.send("USER %s %s * :%s" % (self.nick, self.ident, self.real))
            fake_token = Token.blank_token(self)
            user = structures.User(
                fake_token,
                nick = self.nick,
                ident = self.ident)
            user.update_gecos(self.real)
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

        if self.debug:
            self.log.debug("SEND: %s", data)

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


        self.log.debug("Dispatching comm. pipe to %s" % (get_caller()))

        return self._comm_pipe_send

    def run(self):
        """ py:function:: run(self)

            Runs the parsing/event loop.

            Handles the first message off the top of the send queue and handles what ever data is waiting
            in the subprocess pipe. """

        if not self._connected: return

        while self._connected is True:
            try:
                time.sleep(0.001)
                r, w, e = select.select([self.connection], [], [self.connection], .025)
                if self.connection in r:
                    data = self.connection.recv(8192)
                    if self.debug:
                        self.log.debug("RECV: %s", data)
                    self.parse(data)
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
                self._scheduler.tick()
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
            line = Token(self, line)
            Token.process_events(line)

