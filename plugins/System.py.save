#!/usr/bin/env python

import os, core, sys, logging
from core import get_connection, md5, CorePlugin
from core.CorePlugin import Plugin

class System(Plugin):
    def __init__(self, connection, eventhandler):
        Plugin.__init__(self, connection, eventhandler)
        
        self.eventhandler.get_default_events()['PMEvent'].register(self.handler)
        
        self.identification = get_connection().pluginloader.get_plugin('IdentificationPlugin')
    
    def __deinit__(self):
        self.eventhandler.get_default_events()['PMEvent'].deregister(self.handler)
    
    def handler(self, data):
        assert self.iden
    
        if data.message == (0, 'shutdown'):
            data.origin.message('shutting down.')
            get_connection().shutdown()
        elif data.message == (0, 'reload'):
            get_connection().pluginloader.reload()
            data.origin.message('plugin reload completed!')
        elif data.message == (0, 'rehash'):
            get_connection().configuration.unload()
            get_connection().configuration.load()
            get_connection().pluginloader.reload()
            data.origin.message('rehash completed!')
        
__data__ = {
    'name'    : 'SystemFunctions',
    'version' : '1.0',
    'require' : ['IdentificationPlugin'],
    'main'    : System
}