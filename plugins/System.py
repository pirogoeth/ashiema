#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, core, sys, logging, traceback
from core import Connection, Plugin, Events, HelpFactory
from core.Connection import Connection
from core.Events import Event
from core.Plugin import Plugin
from core.PluginLoader import PluginLoader
from core.HelpFactory import Contexts
from core.HelpFactory import CONTEXT, DESC, PARAMS, NAME, ALIASES
from core.util import Configuration
from core.util.Configuration import Configuration

class SystemEvent(Event):

    def __init__(self):

        Event.__init__(self, "SystemEvent")
        self.__register__()
    
    def match(self, data):

        pass
    
    def run(self, data):

        # System Event codes:
        # 0 -> reload
        # 1 -> shutdown
        # 2 -> rehash
        logging.getLogger('ashiema').info('Waiting for plugins to finish up...')
        for callback in self.callbacks.values():
            callback(data)

class System(Plugin):

    def __init__(self):

        Plugin.__init__(self, needs_dir = False)
        
        self.get_event("PMEvent").register(self.handler)
        self.get_event("PluginsLoadedEvent").register(self.load_identification)
        
        self.system_event = self.get_event("SystemEvent")
        
    def __deinit__(self):

        self.get_event("PMEvent").deregister(self.handler)
        self.get_event("PluginsLoadedEvent").deregister(self.load_identification)
    
    def load_identification(self):

        self.identification = PluginLoader.get_instance().get_plugin('IdentificationPlugin')

    def handler(self, data):

        if data.message == (0, 'shutdown'):
            assert self.identification.require_level(data, 2)
            data.origin.message('Preparing for shutdown...')
            # System event code 1 -> shutdown
            self.eventhandler.fire_once(self.system_event, (1,))
            data.origin.message('Shutting down..')
            Connection.get_instance().shutdown()
        elif data.message == (0, 'reload'):
            assert self.identification.require_level(data, 2)
            # System event code 0 -> reload
            self.eventhandler.fire_once(self.system_event, (0,))
            try:
                PluginLoader.get_instance().reload()
            except Exception, e:
                data.origin.message("Exception %s while reloading plugins." % (e))
                [self.log_error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]
                return
            data.origin.message('Plugins reloaded!')
        elif data.message == (0, 'rehash'):
            assert self.identification.require_level(data, 2)
            # System event code 2 -> rehash
            self.eventhandler.fire_once(self.system_event, (2,))
            Configuration.get_instance().reload()
            data.origin.message('Rehash completed!')

__data__ = {
    'name'    : 'SystemPlugin',
    'version' : '1.0',
    'require' : ['IdentificationPlugin'],
    'main'    : System,
    'events'  : [SystemEvent]
}

__help__ = {
    'shutdown' : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Shuts down the bot safely.',
        PARAMS  : '',
        ALIASES : []
    },
    'reload'   : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Reloads all plugins and loads all new plugins.',
        PARAMS  : '',
        ALIASES : []
    },
    'rehash'   : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Reloads the configuration.',
        PARAMS  : '',
        ALIASES : []
    }
}