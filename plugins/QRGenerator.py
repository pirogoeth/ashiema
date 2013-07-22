#!/usr/bin/env python

import os, logging, core, sys, traceback, shelve, base64, cStringIO
from cStringIO import StringIO
from core import Plugin, Events, util
from core.util import Escapes, unescape, fix_unicode
from core.Plugin import Plugin
from core.PluginLoader import PluginLoader
from core.HelpFactory import Contexts, CONTEXT, PARAMS, DESC, ALIASES
try:
    import qrcode
except (ImportError):
    logging.getLogger('ashiema').error(
        'You must have the py-qrcode module installed.',
        'You can get py-qrcode from http://pypi.python.org/pypi/qrcode/3.0'
    )

HTTPRequestHandler = object

class Base64EncodedStream(object):

    def __init__(self):

        self.__data = ""
    
    def write(self, data):

        self.__data += data
    
    def encode(self):

        return base64.b64encode(self.__data)
    
    def close(self):

        del self.__data, self

class QRGenerator(Plugin):

    def __init__(self):

        Plugin.__init__(self, needs_dir = True, needs_comm_pipe = False)

        self.codes = {}

        self.eventhandler.get_events()['MessageEvent'].register(self.handler)
        self.eventhandler.get_events()['PluginsLoadedEvent'].register(self.__plugins_loaded)
        
        self.__load_codes__()

    def __deinit__(self):

        self.eventhandler.get_events()['MessageEvent'].deregister(self.handler)
        self.eventhandler.get_events()['PluginsLoadedEvent'].deregister(self.__plugins_loaded)
        
        self.__unload_codes__()

    def __load_codes__(self):
    
        try:
            self.codes = shelve.open(self.get_path() + "codes.db", protocol = 0, writeback = True)
        except Exception as e:
            self.codes = {}
            [self.log_error(trace) for trace in traceback.format_exc(4).split('\n')]

    def __unload_codes__(self):
    
        try:
            self.codes.sync()
            self.codes.close()
        except Exception as e:
            [self.log_error(trace) for trace in traceback.format_exc(4).split('\n')]

    def __plugins_loaded(self):

        self.http_server = self.get_plugin('HTTPServer')
        HTTPRequestHandler = self.http_server.get_handler_class()

        class HTTPQrCodeRequestHandler(HTTPRequestHandler):

            def __init__(self, plugin, path = None, route = None):

                HTTPRequestHandler.__init__(self, plugin)

                self.route = route
                self.path = path

            def __call__(self, environment, start_response):

                request = environment['ROUTE_PARAMS'][0]
                print request
                try:
                    mimetype = mimetypes.guess_type(request, strict = False)[0]
                except (Exception) as e:
                    pass
        
        handler = HTTPQrCodeRequestHandler(self, path = "/public", route = r"""/qr/(.+)?$""")
        handler.register()

    def handler(self, data):

        pass

__data__ = {
    'name'      : 'QRGenerator',
    'version'   : '1.0',
    'require'   : ['HTTPServer'],
    'main'      : QRGenerator,
    'events'    : []
}