#!/usr/bin/env python

import os, logging, ashiema, sys, traceback, shelve, random, cStringIO
from cStringIO import StringIO
from contextlib import closing
from ashiema import Plugin, Events, util
from ashiema.util import Escapes, unescape, fix_unicode
from ashiema.Plugin import Plugin
from ashiema.PluginLoader import PluginLoader
from ashiema.HelpFactory import Contexts, CONTEXT, PARAMS, DESC, ALIASES
try:
    import qrcode
except (ImportError):
    logging.getLogger('ashiema').error(
        'You must have the py-qrcode module installed. ' + \
        'You can get py-qrcode from http://pypi.python.org/pypi/qrcode/3.0'
    )

HTTPRequestHandler = object

class Base64EncodedStream(object):

    def __init__(self):

        self.__data = ""
    
    def write(self, data):

        self.__data += data
    
    def encode(self):

        return self.__data.encode('base64')
    
    def close(self):

        del self.__data, self

class QRGenerator(Plugin):

    def __init__(self):

        Plugin.__init__(self, needs_dir = True, needs_comm_pipe = False)

        self.codes = shelve.Shelf({})

        self.get_event("MessageEvent").register(self.handler)
        self.get_event("PluginsLoadedEvent").register(self.__load_identification)
        self.get_event("HTTPServerHandlerRegistrationReady").register(self.__http_server_ready)
        
        self.__load_codes__()

    def __deinit__(self):

        self.get_event("MessageEvent").deregister(self.handler)
        self.get_event("PluginsLoadedEvent").deregister(self.__load_identification)
        self.get_event("HTTPServerHandlerRegistrationReady").deregister(self.__http_server_ready)
        
        self.__unload_codes__()
    
    def __load_identification(self):
    
        self.identification = self.get_plugin('IdentificationPlugin')

    def __load_codes__(self):
    
        try:
            self.codes = shelve.open(self.get_path() + "codes.db", protocol = 0, writeback = True)
        except Exception as e:
            self.codes = shelve.Shelf({})
            [self.log_error(trace) for trace in traceback.format_exc(4).split('\n')]

    def __unload_codes__(self):
    
        try:
            self.codes.sync()
            self.codes.close()
        except Exception as e:
            [self.log_error(trace) for trace in traceback.format_exc(4).split('\n')]

    def __gen_identifier__(self, length = 8):
    
        return "".join([random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890') for n in xrange(length)])

    def __http_server_ready(self, data = None):

        self.http_server = self.get_plugin('HTTPServer')
        HTTPRequestHandler = self.http_server.get_handler_class()

        class HTTPQrCodeRequestHandler(HTTPRequestHandler):

            def __init__(self, plugin, path = None, route = None):

                HTTPRequestHandler.__init__(self, plugin)

                self.route = route
                self.path = path
                self.templating = plugin.get_plugin('HTTPServer').get_templater_class()

            def __call__(self, environment, start_response):

                request = environment['ROUTE_PARAMS'][0]
                try:
                    try:
                        rendered = StringIO()
                        templater = self.templating()
                        with closing(shelve.open(self.plugin.get_path() + "codes.db", protocol = 0, writeback = True)) as codes:
                            code = codes[request]
                        with closing(open(self.plugin.get_path() + 'qrcode.thtml', 'r')) as template:
                            try: start_response(self.response_codes['OK'], [('Content-Type', 'text/html')])
                            except: pass
                            templater.update_globals({
                                'path'      : environment.get('PATH_INFO', ''),
                                'env'       : environment,
                                'qrid'      : request,
                                'code'      : code
                            })
                            templater.options()['input'] = template
                            templater.options()['output'] = rendered
                            templater.parse()
                        for line in rendered.getvalue().split('\n'):
                            yield line
                    except Exception as e:
                        raise
                except Exception as e:
                    raise
        
        handler = HTTPQrCodeRequestHandler(self, path = "/", route = r"""qr/(.+)?$""")
        handler.register()
    
    def __encode(self, input):
    
        id = self.__gen_identifier__(length = 6)
        while id in self.codes:
            id = self.__gen_identifier__(length = 6)
        
        qr = qrcode.QRCode(
            version             = 1,
            error_correction    = qrcode.constants.ERROR_CORRECT_L,
            box_size            = 10,
            border              = 2)
        qr.add_data(input)
        qr.make(fit = True)
        
        imgdata = qr.make_image()
        stream = Base64EncodedStream()
        imgdata.save(stream)
        
        data = stream.encode()
        stream.close()
        
        self.codes.update({id: data})
        self.codes.sync()
        
        return id

    def handler(self, data):

        if data.message == (0, '@qr-encode'):
            assert self.identification.require_level(data, 1)
            try:
                if len(data.message[1:]) > 1:
                    input = " ".join(data.message[1:])
                else:
                    input = data.message[1]
            except (IndexError) as e:
                data.origin.notice("%s[QRGenerator]: %sPlease provide a string to encode." % (Escapes.LIGHT_BLUE, Escapes.GREEN))
                return
            data.origin.notice("%s[QRGenerator]: %sEncoding..." % (Escapes.LIGHT_BLUE, Escapes.GREEN))
            qrid = self.__encode(input)
            data.origin.notice("%s[QRGenerator]: %s/qr/%s" % (Escapes.LIGHT_BLUE, self.get_plugin('HTTPServer').get_base_url(), qrid))
            

__data__ = {
    'name'      : 'QRGenerator',
    'version'   : '1.0',
    'require'   : ['IdentificationPlugin', 'HTTPServer'],
    'main'      : QRGenerator,
    'events'    : []
}

__help__ = {
    '@qr-encode' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Generates a QR code from given input.',
        PARAMS  : '<input>',
        ALIASES : []
    }
}