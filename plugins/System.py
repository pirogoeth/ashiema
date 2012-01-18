#!/usr/bin/env python

import os, core, sys, logging
from core import get_connection, md5, CorePlugin
from core.CorePlugin import Plugin

class System(Plugin):
    def __init__(self, connection, eventhandler):
        Plugin.__init__(self, connection, eventhandler)
        
        self.eventhandler.get_default_events()['PMEvent'].register(self.handler)
        self.eventhandler.get_default_events()['PluginsLoadedEvent'].register(self.load_identification)
        
    def __deinit__(self):
        self.eventhandler.get_default_events()['PMEvent'].deregister(self.handler)
        self.eventhandler.get_default_events()['PluginsLoadedEvent'].deregister(self.load_identification)
    
    def load_identification(self):
        self.identification = get_connection().pluginloader.get_plugin('IdentificationPlugin')

    def handler(self, data):
        if data.message == (0, 'shutdown'):
            assert self.identification.require_level(data, 2)
            data.origin.message('shutting down.')
            get_connection().shutdown()
        elif data.message == (0, 'rehash'):
            assert self.identification.require_level(data, 2)
            get_connection().configuration.unload()
            get_connection().configuration.load()
            data.origin.message('rehash completed!')
        
__data__ = {
    'name'    : 'SystemFunctions',
    'version' : '1.0',
    'require' : ['IdentificationPlugin'],
    'main'    : System
}