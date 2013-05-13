#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, core, sys, logging, traceback
from core import get_connection, md5, Plugin, Event, HelpFactory
from core.Plugin import Plugin
from core.HelpFactory import Contexts
from core.HelpFactory import CONTEXT, DESC, PARAMS, NAME, ALIASES

class SystemEvent(Event.Event):

    def __init__(self, eventhandler):
        Event.Event.__init__(self, eventhandler, "SystemEvent")
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

    def __init__(self, connection, eventhandler):

        Plugin.__init__(self, connection, eventhandler, needs_dir = False)
        
        self.eventhandler.get_events()['PMEvent'].register(self.handler)
        self.eventhandler.get_events()['PluginsLoadedEvent'].register(self.load_identification)
        
        self.system_event = self.eventhandler.get_events()['SystemEvent']
        
    def __deinit__(self):

        self.eventhandler.get_events()['PMEvent'].deregister(self.handler)
        self.eventhandler.get_events()['PluginsLoadedEvent'].deregister(self.load_identification)
    
    def load_identification(self):

        self.identification = get_connection().pluginloader.get_plugin('IdentificationPlugin')

    def handler(self, data):

        if data.message == (0, 'shutdown'):
            assert self.identification.require_level(data, 2)
            data.origin.message('Preparing for shutdown...')
            # System event code 1 -> shutdown
            self.eventhandler.fire_once(self.system_event, (1,))
            data.origin.message('Shutting down..')
            get_connection().shutdown()
        elif data.message == (0, 'reload'):
            assert self.identification.require_level(data, 2)
            # System event code 0 -> reload
            self.eventhandler.fire_once(self.system_event, (0,))
            try:
                get_connection().pluginloader.reload()
            except Exception, e:
                data.origin.message("Exception %s while reloading plugins." % (e))
                [logging.getLogger("ashiema").error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]
                return
            data.origin.message('Plugins reloaded')
        elif data.message == (0, 'rehash'):
            assert self.identification.require_level(data, 2)
            # System event code 2 -> rehash
            self.eventhandler.fire_once(self.system_event, (2,))
            get_connection().configuration.reload()
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