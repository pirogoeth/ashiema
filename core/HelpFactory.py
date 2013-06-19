#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

CONTEXT = "context"
DESC = "desc"
PARAMS = "params"
ALIASES = "aliases"
NAME = "name"

class Contexts(object):
    
    PUBLIC  = "public"
    PRIVATE = "private"
    BOTH = "both"

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
    
    def _both(entry):

        if entry[CONTEXT] is Contexts.BOTH:
            return True
        else:
            return False

    PUBLIC = _public
    PRIVATE = _private
    BOTH = _both

class HelpFactory(object):
    """ Stores help information for plugins and provides a simple interface to retrieve stored help data. """

    __instance = None

    @staticmethod
    def get_instance():
        
        if HelpFactory.__instance is None:
            return HelpFactory()
        else:
            return HelpFactory.__instance

    def __init__(self):
    
        HelpFactory.__instance = self

        self._help = {}
    
    def register(self, plugin, help):

        self._help[plugin] = help
    
    def deregister(self, plugin):

        del self._help[plugin]
    
    def getHelpForPlugin(self, plugin):

        if not self._help.__contains__(plugin):
            yield None

        for key, entry in self._help[plugin].iteritems():
            entry.update({NAME : key})
            yield entry
    
    def getHelp(self, filter_func = None):

        results = []
        
        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({NAME : key})
                results.append(entry)
        
        for entry in filter(filter_func, results):
            yield entry

    def getAllPublicHelp(self):

        results = []

        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({NAME : key})
                results.append(entry)

        for entry in filter(Filters.PUBLIC, results):
            yield entry

    def getAllPrivateHelp(self):

        results = []

        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({NAME : key})
                results.append(entry)

        for entry in filter(Filters.PRIVATE, results):
            yield entry
    
    def getDualContextHelp(self):

        results = []
        
        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({NAME : key})
                results.append(entry)
        
        for entry in filter(Filters.BOTH, results):
            yield entry