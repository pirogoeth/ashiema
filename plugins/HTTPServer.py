#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, sys, re, cgi, wsgiref
from core import Plugin, Event, get_connection, util
from core.util import Escapes, unescape
from core.Plugin import Plugin
from contextlib import closing
from cgi import parse_qs, escape
from wsgiref.simple_server import make_server

class HTTPServer(Plugin):

    """ This is an HTTP server using WSGI and custom middlewares to provide a web interface for running instances of the bot.
        Each instance will have it's own HTTP server, if enabled, and each plugin that is loaded into the bot is allowed to 
        allocate a path on the server to server it's own content, such as status, a generic (or comprehensive, plugin developer's choice...) web interface,
        a configuration interface, or even a remote API for fetching data. Each plugin MAY allocate more than one route, but for each route
        that is allocated, the plugin must have a corresponding HTTPRequestHandler implemented.

        For the HTTP server to be set up correctly, the bot administrator must add a block to the server configuration with the following structure:

            HTTPServer {
                bind_host = 'localhost' # either localhost or another interface, must provide the IP of the interface to bind to..
                bind_port = 8000 # must be available AND must be > 1024 if not running as root.
                resource_dir = '/public' # directory inside the HTTPServer's plugin directory where static resources will be served from.
                resource_path = '/public' # path that +resource_dir+ can be accessed from.
            }

        Path allocation will be handled by this plugin automatically after all HTTPRequestHandlers are registered.
    """

    def __init__(self, connection, eventhandler):

        Plugin.__init__(self, connection, eventhandler, needs_dir = True)

        self.config = self.get_plugin_configuration()
        if len(self.config) == 0:
            raise Exception("You must configure options for the HTTP server in your server config!")

        self.request_handlers = {}
        self.running = False

        self.eventhandler.get_events()['MessageEvent'].register(self.handler)
    
    def __deinit__(self):
        
        if self.running:
            self.__stop()
        
        for handler in self.request_handlers.values():
            handler.shutdown()
        
        self.eventhandler.get_events()['MessageEvent'].deregister(self.handler)
    
    def __get_handler_name__(self, handler):
        
        return type(handler).__name__
    
    def __start(self):
        
        if self.running:
            return
        
        bind_host = self.config['bind_host']
        bind_port = self.config['bind_port']
        resource_dir = self.config['resource_dir']
    
    def __stop(self):
        
        if not self.running:
            return
    
    def register_handler(self, handler):
        
        self.request_handlers.update({ self.__get_handler_name__(handler): handler })
    
    def deregister_handler(self, handler):
        
        self.request_handlers.remove(self.__get_handler_name__(handler))
        
    def server_application(self, environment, start_response):
        
        pass

class HTTPRequestHandler(object):
    pass

class HTTPDInitEvent(Event):
    
    """ This event is fired when the HTTPD is about to initialise.
        This is used to let plugins know when to register their HTTPRequestHandlers so that all requests will be ready
        on-time.
    """
    
    def __init__(self, eventhandler):
        
        Event.__init__(self, eventhandler, "HTTPDInitEvent")
        self.__register__()
        
    def match(self, data):
        
        pass
    
    def run(self, data):
        
        for callback in self.callbacks.values():
            callback(data)

class Templating(object):

    """ This is a template parsing class, which will be used in conjunction with ashiema's HTTP server to serve templated
        HTML pages that have the ability to provide plugin-specific information.  By default, templating will work as follows:
        
        Interpolation:
            %{ statement; }
        
            Interpolation applies to variables and statements, so input from anything can be used in-line.
        
        Flow Control:
            = if whatever is something or something is None
              do things...
            = else
              do something else..
            back to first level content.
            
            Flow control blocks use indentation to determine when to break into a separate block.
            
            = for item in items
              ...
            
            = while some_condition
              ...
    """
    
    def __init__(self,
                 interpolation_regex = re.compile(r"%\{([^%\{|\}]+)\}", re.VERBOSE),
                 block_regex = re.compile(r"(?:\s+)?=\s+?([^%\{\}\r\n]+):?", re.VERBOSE),
                 preprocessor = (lambda data, option: data.lstrip()),
                 globals_dict = {},
                 exc_handle = None):

        # regexes for matching template statements
        self.interpol_regex = interpolation_regex
        self.block_regex = block_regex
        
        # function used to process data before handling it
        self.preprocessor = preprocessor
        
        # function that handles exceptions
        self.exc_handler = exc_handle if exc_handle is not None else self.__exc_handle__
        
        # variables to make available to the scope of the templated page
        self.globals = globals_dict
        self.locals = { '_parse': self._parseblock_ }
        
        # keywords that are allowed to be used to lead blocks
        self.allowed_blocks = ['for', 'while', 'if', 'elif', 'else']
        
        # the two types of whitespace we care about
        self._space = " "
        self._tab = "\t"
        
        # options
        self.__options = {
            'indent_type'           : 's', # type of indents, 's' for spaces, 't' for tabs
            'block_indent_size'     : 2, # size of the content indent inside blocks
            'block_char'            : '=', # character used to mark beginning of a block, same that is given in the regex
            'debugging'             : False, # do i print debugging information?
            'input'                 : sys.stdin, # alternate input if  is not given to +parse()+
            'output'                : sys.stdout # output for parsed data
        }
    
    def __exc_handle__(self, exc_str):

        raise Exception(exc_str)
        
    def _count_whitespace_(self, statement):
    
        if self.options()['indent_type'].lower() == 's':
            return len(statement) - len(statement.lstrip(self._space))
        elif self.options()['indent_type'].lower() == 't':
            return len(statement) - len(statement.lstrip(self._tab))
        else:
            self.options()['indent_type'] = 's'
            return self._count_whitespace_(statement)
    
    def _parseblock_(self, pos = 0, last_pos = None):

        def repl(match, self = self):
            expr = self.preprocessor(match.group(1), 'eval')
            try: return str(eval(expr, self.globals, self.locals))
            except: return str(self.exc_handler(expr))
        
        block = self.locals['_block']

        if last_pos is None:
            last_pos = len(block)
        
        while pos < last_pos:
            line = block[pos]
            match = self.block_regex.match(line)
            if match:
                stmt = match.group(1)
                if self.options()['debugging']:
                    print "matched: [" + stmt + "] from line: {" + line + "}, indent size: " + str(line.index(self.options()['block_char']))
                eind_size = line.index(self.options()['block_char'])
                eind_size += self.options()['block_indent_size']
                search = pos + 1
                nest = 1
                while search < last_pos:
                    line = block[search]
                    ind_size = self._count_whitespace_(line)
                    if ind_size >= eind_size: # we have an indentation after our block
                        search += 1
                    else:
                        nest -= 1
                        if nest == 0:
                            break
                stmt = self.preprocessor(stmt, 'exec')
                if self.options()['debugging']:
                    print "executing statement: [" + stmt + "]" # debug
                if search - (pos + 1) == 0:
                    stmt = '%s' % stmt
                else:
                    if stmt[len(stmt) - 1] != ':':
                        stmt += ':'
                    stmt = '%s _parse(%s, %s)' % (stmt, pos + 1, search)
                exec stmt in self.globals, self.locals
                pos = search
            else:
                self.options()['output'].write(self.interpol_regex.sub(repl, line) + "\n")
                pos += 1

    def options(self):
        
        return self.__options

    def parse(self, block = None):
        
        if block is None:
            block = self.options()['input'].readlines()
        
        self.locals['_block'] = block
        
        self._parseblock_()

__data__ = {
    'name'      : 'HTTPServer',
    'version'   : '1.0',
    'require'   : ['IdentificationPlugin'],
    'main'      : HTTPServer,
    'events'    : [HTTPDInitEvent]
}
