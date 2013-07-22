#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, sys, re, cgi, wsgiref, errno, time, logging, mimetypes, datetime, pprint, StringIO
from core import Plugin, Events, util
from core.util import Escapes, unescape, fork
from core.Events import Event
from core.Plugin import Plugin
from core.HelpFactory import Contexts
from core.HelpFactory import CONTEXT, DESC, PARAMS, ALIASES
from contextlib import closing
from cgi import parse_qs, escape
from datetime import datetime
from sys import exc_info
from traceback import format_tb
from StringIO import StringIO
from multiprocessing import Process, Manager
from wsgiref.simple_server import make_server

class HTTPServer(Plugin):

    """ This is an HTTP server using WSGI and custom middlewares to provide a web interface for running instances of the bot.
        Each instance will have it's own HTTP server, if enabled, and each plugin that is loaded into the bot is allowed to 
        allocate a path on the server to server it's own content, such as status, a generic (or comprehensive, plugin developer's choice...) web interface,
        a configuration interface, or even a remote API for fetching data. Each plugin MAY allocate more than one route, but for each route
        that is allocated, the plugin must have a corresponding HTTPRequestHandler implemented.

        For the HTTP server to be set up correctly, the bot administrator must add a block to the server configuration with the following structure:

            HTTPServer {
                bind_host = localhost # either localhost or another interface, must provide the IP of the interface to bind to..
                bind_port = 8000 # must be available AND must be > 1024 if not running as root.
                autostart = False # whether we start immediately past init or not.
                resource_path = /public # directory inside the HTTPServer's plugin directory where static resources will be served from.
                resource_route = /public # path that +resource_dir+ can be accessed from.
                development = False # mode that the server will run in. true is production, false is development.
            }

        Path allocation will be handled by this plugin automatically after all HTTPRequestHandlers are registered.
    """

    def __init__(self):

        Plugin.__init__(self, needs_dir = True, needs_comm_pipe = True)

        HTTPServer.running = False
        self.request_handlers = dict()

        self.config = self.get_plugin_configuration()
        
        self.__vars__ = {
            'resources' : self.config['resource_path']
        }
        
        if len(self.config) == 0:
            raise Exception("You must configure options for the HTTP server in your server config!")

        self.resource_dir = self.config['resource_path']

        if self.resource_dir[0] == '/':
            self.resource_dir = self.resource_dir[1:]
        
        self.resource_path = self.get_path() + self.resource_dir

        self.resource_route = self.config['resource_route']
        
        if self.resource_route[0] == '/':
            self.resource_route = self.resource_route[1:]
        
        if not os.path.exists(self.resource_path):
            try:
                os.makedirs(self.resource_path)
            except (OSError) as e:
                if e.errno != errno.EEXIST:
                    raise
        
        self.__process = None
        
        self.__load_layers()

        self.eventhandler.get_events()['MessageEvent'].register(self.handler)
        self.eventhandler.get_events()['PluginsLoadedEvent'].register(self.__on_plugins_loaded)

    def __deinit__(self):
        
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__

        if HTTPServer.running:
            self.__stop()
        
        self.eventhandler.get_events()['MessageEvent'].deregister(self.handler)
        self.eventhandler.get_events()['PluginsLoadedEvent'].deregister(self.__on_plugins_loaded)

    def __on_plugins_loaded(self):
        
        self.identification = self.get_plugin('IdentificationPlugin')

        self.__register_resource_handler(self.resource_path, self.resource_route)

        if self.config['autostart']:
            self.__start()
    
    def __start(self):
        
        if HTTPServer.running:
            return
        
        bind_host = self.config['bind_host']
        bind_port = int(self.config['bind_port'])
        
        HTTPServer.running = True
        
        self.__start_serve(bind_host, bind_port)
    
    def __start_serve(self, host, port):
    
        class WSGIServerProcess(Process):
        
            def __init__(self, host, port, router, gethandlers):

                Process.__init__(self, name = "ashiema WSGI/HTTP server process")

                self.host = host
                self.port = port
                self.active = False
                self.daemon = True
                self.__router = router
                self.__server = make_server(self.host, self.port, self.__router)
                
                print str(gethandlers())

            def set_active(self, active):

                self.active = active
            
            def run(self):

                self.active = True
                while self.active:
                    try:
                        time.sleep(0.00025)
                        self.__server.handle_request()
                    except (SystemExit, KeyboardInterrupt) as e:
                        self.__server.server_close()
                        self.__server.socket.close()
                        return
                logging.getLogger('ashiema').info('HTTPServer no longer active.')
                self.__server.server_close()
                self.__server.socket.close()

        self.__process = WSGIServerProcess(host, port, self.__router, self.__get_reqhands)
        self.__process.start()
        self.log_debug("Started WSGI server in child process [ID: %s]." % (self.__process.pid))

    def __get_reqhands(self):
    
        return self.request_handlers.values()

    def __stop(self):
        
        if not HTTPServer.running or not self.__process:
            return
        
        HTTPServer.running = False

        self.log_info("Deactivating HTTP server...")
        self.__process.set_active(False)

        self.log_info("Terminating child process...")
        self.__process.terminate()
        
        del self.__process
    
    def __restart(self):
    
        if not HTTPServer.running:
            self.log_error("Can not restart, HTTPServer is not running.", "Use __start() to launch the HTTPServer.")
            return
        
        self.__stop()
        
        self.log_info("Restarting HTTPServer...")
        
        self.__start()

    def __load_layers(self):
    
        # load the exception layer
        dev_mode = False if self.config['development'] == 'False' else True
        self.__router = ExceptionLayer(self.__router, development = dev_mode, exc_template = self.get_path() + "exception.thtml")

    def __router(self, environment, start_response):
        
        request_path = environment.get('PATH_INFO', '').lstrip('/')

        print self.request_handlers.values()

        for handler in self.request_handlers.values():
            match = re.search(handler.get_raw_route(), request_path)
            if match is not None:
                environment['ROUTE_PARAMS'] = match.groups()
                return handler(environment, start_response)

        return self._not_found(environment, start_response)
    
    def _not_found(self, environment, start_response):
        
        def render_404_template():
            rendered = StringIO()
            templater = Templating()
            with closing(open(self.get_path() + '404.thtml', 'r')) as template:
                try:
                    start_response('404 NOT FOUND', [
                                    ('Content-Type', 'text/html')])
                except: pass
                templater.update_globals({
                    'path'          : environment.get('PATH_INFO', ''),
                    'env'           : environment
                })
                templater.update_globals(self.__vars__)
                templater.options()['input'] = template
                templater.options()['output'] = rendered
                templater.parse()
            return rendered
            
        for line in render_404_template().getvalue().split('\n'):
            yield line
    
    def __register_resource_handler(self, resource_path, resource_route):
        """ registers the statics handler for +resource_path+. """
        
        class HTTPResourceHandler(HTTPRequestHandler):
            
            def __init__(self, plugin, path = None, route = None):
                
                HTTPRequestHandler.__init__(self, plugin)
                
                self.route = route
                self.path = path
            
            def __call__(self, environment, start_response):
                
                request = environment['ROUTE_PARAMS'][0]
                try:
                    mimetype = mimetypes.guess_type(request, strict = False)[0]
                    with closing(open(self.path + "/" + request, 'r')) as resource:
                        start_response(self.response_codes['OK'], [
                                        ('Content-Type', mimetype)])
                        data = resource.read()
                        for line in data.split('\n'):
                            yield line + "\n"
                except (Exception) as e:
                    for line in self.plugin._not_found(environment, start_response):
                        yield line
        
        resource_handler = HTTPResourceHandler(self, path = resource_path, route = resource_route)
        resource_handler.register()

    def handler(self, data):
    
        if data.message == (0, '@httpd-start'):
            assert self.identification.require_level(data, 2)
            if HTTPServer.running:
                data.respond_to_user("The HTTP server is already running.")
            elif not HTTPServer.running:
                self.__start()
                data.respond_to_user("The HTTP server is starting...")
        elif data.message == (0, '@httpd-stop'):
            assert self.identification.require_level(data, 2)
            if not HTTPServer.running:
                data.respond_to_user("The HTTP server is not running.")
            elif HTTPServer.running:
                self.__stop()
                data.respond_to_user("The HTTP server is stopping...")
        elif data.message == (0, '@httpd-status'):
            assert self.identification.require_level(data, 1)
            if HTTPServer.running:
                data.respond_to_user("The HTTP server is currently active.")
                data.respond_to_user("Content is being served at %s:%s." % (self.config['bind_host'], self.config['bind_port']))
            elif not HTTPServer.running:
                data.respond_to_user("The HTTP server is currently inactive.")
        
    def register_handler(self, handler):
        
        for reg_handler in self.request_handlers.values():
            if handler.get_raw_route() == reg_handler.get_raw_route():
                self.log_error("HTTPRequestHandler [" + handler.get_name() + "] tried to register the same HTTP route as handler [" + reg_handler.get_name() + "]!")
                return

        self.request_handlers.update({ handler.get_name(): handler })
    
    def deregister_handler(self, handler):
        
        self.request_handlers.remove(handler.get_name())

    def get_handler_class(self):

        return HTTPRequestHandler

    def get_templater_class(self):

        return Templating

class HTTPRequestHandler(object):

    """ This is a handler that provides the response to an HTTP request.
        Each request handler is bound to a single route, where the route is a regular
        expression.
    """
    
    def __init__(self, plugin):
    
        self.name = type(self).__name__
        self.plugin = plugin
        self.templater = Templating()
        self.route = (self.name + r'/?$') if not hasattr(self, 'route') else self.route
        self.response_codes = {
            'OK'                    : "200 OK",
            'BAD_REQUEST'           : "400 BAD REQUEST",
            'UNAUTHORIZED'          : "401 UNAUTHORIZED",
            'FORBIDDEN'             : "403 FORBIDDEN",
            'NOT_FOUND'             : "404 NOT FOUND",
            'TEAPOT'                : "418 I'M A TEAPOT",
            'SERVER_ERROR'          : "500 INTERNAL SERVER ERROR",
            'NOT_IMPLEMENTED'       : "501 NOT IMPLEMENTED"
        }
    


    def get_name(self):

        return self.name

    def register(self):
        
        self.plugin.get_plugin('HTTPServer').register_handler(self)
    
    def deregister(self):
    
        self.plugin.get_plugin('HTTPServer').deregister_handler(self)
    
    def get_route(self):
    
        return re.compile(self.route)
    
    def get_raw_route(self):
    
        return self.route

class ExceptionLayer(object):

    """ A layer that wraps the application server and catches exceptions and displays them, can be filtered between production and development. """
    
    def __init__(self, application, development = False, exc_template = "exception.thtml"):
    
        self.application = application
        self.development = development
        self.templater = Templating()
        self.exception_template = exc_template
    
    def __call__(self, environment, start_response):

        def render_exception_template():
            rendered = StringIO()
            with closing(open(self.exception_template, 'r')) as template:
                try:
                    start_response('500 INTERNAL SERVER ERROR', [
                                    ('Content-Type', 'text/html')])
                except: pass
                self.templater.update_globals({
                    'type'      : type,
                    'value'     : value,
                    'traceback' : traceback,
                    'path'      : environment.get('PATH_INFO', '')
                })
                self.templater.options()['input'] = template
                self.templater.options()['output'] = rendered
                self.templater.parse()
            return rendered

        response = None
        try:
            response = self.application(environment, start_response)
            for line in response:
                yield line
        except:
            type, value, trace = exc_info()
            traceback = ['An error occurred while serving your request:']
            if self.development:
                traceback += ['','Traceback (most recent call last):']
                traceback += format_tb(trace)
            traceback.append('%s: %s' % (type.__name__, value))
            try:
                for line in render_exception_template().getvalue().split('\n'):
                    yield line
            except:
                for line in render_exception_template().getvalue().split('\n'):
                    yield line
        if hasattr(response, 'close'):
            response.close()

class Templating(object):

    """ This is a template parsing class, which will be used in conjunction with ashiema's HTTP server to serve templated
        HTML pages that have the ability to provide plugin-specific information.  By default, templating will work as follows:
        
        Interpolation:
            %{ statement; }
        
            Interpolation applies to variables and statements, so basically anything that returns a value can be used in-line.
        
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
            'block_char'            : '=', # character used to mark beginning of a block, same that is given in the block regex
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
                    logging.getLogger('ashiema').debug("[Templating] matched: [" + stmt + "] from line: {" + line + "}, indent size: " + str(line.index(self.options()['block_char'])))
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
                    logging.getLogger('ashiema').debug("[Templating] executing statement: [" + stmt + "]")
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
    
    def update_globals(self, new_globals):
    
        self.globals.update(new_globals)

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
    'events'    : []
}

__help__ = {
    '@httpd-start' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Makes the HTTP server start serving on the designated host and port.',
        PARAMS  : '',
        ALIASES : []
    },
    '@httpd-stop' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Makes the HTTP server stop serving.',
        PARAMS  : '',
        ALIASES : []
    },
    '@httpd-status' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Displays the current status of the HTTP server.',
        PARAMS  : '',
        ALIASES : []
    }
}
