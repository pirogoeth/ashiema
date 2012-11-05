#!/usr/bin/env python

# constants for making __help__ dicts...just in case stuff chances in the future.

CONTEXT = "context"
DESC = "desc"
PARAMS = "params"

class Contexts(object):
    
    PUBLIC  = "public"
    PRIVATE = "private"

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

    def getPublicHelp(self):
        results = []

        def filter_pub(entry):
            if entry[CONTEXT] is Contexts.PUBLIC:
                return True
            else:
                return False

        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({'name' : key})
                results.append(entry)

        for entry in filter(filter_pub, results):
            yield entry

    def getPrivateHelp(self):
        results = []

        def filter_priv(entry):
            if entry[CONTEXT] is Contexts.PRIVATE:
                return True
            else:
                return False

        for plugin in self._help.keys():
            for key, entry in self._help[plugin].iteritems():
                entry.update({'name' : key})
                results.append(entry)

        for entry in filter(filter_priv, results):
            yield entry