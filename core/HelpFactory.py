#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

# constants for making __help__ dicts...just in case stuff changes in the future.

CONTEXT = "context"
DESC = "desc"
PARAMS = "params"
ALIASES = "aliases"

class Contexts(object):
    
    PUBLIC  = "public"
    PRIVATE = "private"

class Filters(object):

    def _public(entry):
        if entry[CONTEXT] is Contexts.PUBLIC:
            return True
        else:
            return False
    
    def _private(entry):
        if entry[CONTEXT] is Contexts.PRIVATE:
            return True
        else:
            return False

    PUBLIC = _public
    PRIVATE = _private

class HelpFactory(object):

    def __init__(self):
        self._help = {}
    
    def register(self, plugin, help):
        self._help[plugin] = help
    
    def deregister(self, plugin):
        del self._help[plugin]
    
    def getHelpForPlugin(self, plugin):
        for key, entry in self._help[plugin].iteritems():
            entry.update({'name' : key})
            yield entry
    
    def getHelp(self, filter_func = None):
        results = []
        
        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({'name' : key})
                results.append(entry)
        
        for entry in filter(filter_func, results):
            yield entry

    def getHelpByFilter(self, filter_func):
        results = []
        
        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({'name': key})
                results.append(entry)
        
        for entry in filter(filter_func, results):
            yield entry
    
    def getFilteredHelpForPlugin(self, plugin, filter_func):
        results = []
        
        for key, entry in self._help[plugin].iteritems():
            entry.update({'name': key})
            results.append(entry)
        
        for entry in filter(filter_func, results):
            yield entry

    def getAllPublicHelp(self):
        results = []

        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({'name' : key})
                results.append(entry)

        for entry in filter(Filters.PUBLIC, results):
            yield entry

    def getAllPrivateHelp(self):
        results = []

        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({'name' : key})
                results.append(entry)

        for entry in filter(Filters.PRIVATE, results):
            yield entry