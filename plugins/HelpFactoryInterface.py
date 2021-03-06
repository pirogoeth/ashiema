#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, logging, ashiema
from ashiema import Plugin, Events, util
from ashiema.util import Escapes
from ashiema.Plugin import Plugin
from ashiema.HelpFactory import Contexts, Filters, HelpFactory
from ashiema.HelpFactory import CONTEXT, PARAMS, DESC, NAME, ALIASES

class HelpFactoryInterface(Plugin):

    def __init__(self):
        
        Plugin.__init__(self, needs_dir = False)
        
        self.helpfactory = HelpFactory.get_instance()
        
        self.get_event("MessageEvent").register(self.handler)
        self.get_event("PMEvent").register(self.handler)
    
    def __deinit__(self):
    
        self.get_event("MessageEvent").deregister(self.handler)
        self.get_event("PMEvent").deregister(self.handler)
    
    def handler(self, data):

        if ((data.message == (0, 'help') or data.message == (0, '@help')) and data.target.is_self()) or (data.message == (0, '@help') and not data.target.is_self()):
            if data.message.has_index(1): # there is an argument.
                data.origin.notice("Help for %s%s%s." % (Escapes.BOLD, data.message[1], Escapes.BOLD))
                for entry in self.helpfactory.getHelpForPlugin(data.message[1]):
                    if entry is None:
                        data.origin.notice("There is no help for %s%s%s." % (Escapes.BOLD, data.message[1], Escapes.BOLD))
                    data.origin.notice("%s%s%s: %s" % (Escapes.BOLD, entry[NAME], Escapes.BOLD, entry[DESC]))
                    data.origin.notice(" - Context: %s" % (entry[CONTEXT]))
                    data.origin.notice(" - Aliases: %s" % (entry[ALIASES] if entry.__contains__(ALIASES) else []))
                    data.origin.notice(" - Parameters: %s" % (entry[PARAMS] if entry[PARAMS] is not '' else 'None!'))
            elif not data.message.has_index(1): # no arguments
                data.origin.notice("Help topics:")
                for entry in self.helpfactory._help.keys():
                    data.origin.notice(" - %s%s%s" % (Escapes.BOLD, entry, Escapes.BOLD))
                data.origin.notice("End of topic list.")
                    

__data__ = {
    'name'      : 'HelpFactoryInterface',
    'version'   : '1.0',
    'require'   : [],
    'main'      : HelpFactoryInterface,
    'events'    : []
}

__help__ = {
    'help'  : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Lists plugins to retrieve help for, or, if a plugin name is provided, help for all available commands will be shown.',
        PARAMS  : '[plugin]',
        ALIASES : ['@help']
    },
    '@help'  : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Lists plugins to retrieve help for, or, if a plugin name is provided, help for all available commands will be shown.',
        PARAMS  : '[plugin]',
        ALIASES : []
    }
}