# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013-2015 Sean Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import ashiema, datetime, htmlentitydefs, malibu, os, re, traceback

from ashiema.api.events import Event
from ashiema.api.help import Contexts, CONTEXT, DESC, PARAMS, ALIASES
from ashiema.api.plugin import Plugin
from ashiema.plugin.loader import PluginLoader
from ashiema.util import Escapes, unescape

from datetime import timedelta
from malibu.database.dbmapper import DBMapper
from malibu.util.log import LoggingDriver
from urllib import urlopen, urlencode


class UrbanDictionary(Plugin):

    def __init__(self):
    
        Plugin.__init__(self, needs_dir = False)
        
        self.cache = {}
        
        self.get_event("MessageEvent").register(self.handler)
        self.get_event("PluginsLoadedEvent").register(self._load_identification)
        
        self.__clean_cache_job = self.scheduler.create_job(
            "UrbanDictionary__scheduled_cache_clean", self.clean_cache, timedelta(days = 1), recurring = True)
        
        self.url = "http://api.urbandictionary.com/v0/define?"
    
    def __deinit__(self):
    
        self.get_event("MessageEvent").deregister(self.handler)
        self.get_event("PluginsLoadedEvent").deregister(self._load_identification)

        self.scheduler.remove_job(self.__clean_cache_job)
        
    def _load_identification(self):
    
        self.identification = PluginLoader.get_instance().get_plugin("IdentificationPlugin")
    
    def clean_cache(self):
    
        self.cache.clear()
    
    def handler(self, data):
    
        if data.message == (0, "@ud") or data.message == (0, "urbandictionary"):
            try:
                term = " ".join(data.message[1:])
            except (IndexError):
                data.target.message("%s[UrbanDictionary]: %sPlease provide a term to search for." % (Escapes.AQUA, Escapes.BOLD))
                return
            self.beginQuery(data, term)
        elif data.message == (0, "@ud-cache") or data.message == (0, "urbandictionary-cache"):
            assert self.identification.require_level(data, 1)
            data.target.message("%s[UrbanDictionary]: %s objects cached." % (Escapes.AQUA, len(self.cache)))
            return
        elif data.message == (0, "@ud-cache-clear") or data.message == (0, "urbandictionary-cacheclear"):
            assert self.identification.require_level(data, 1)
            self.clean_cache()
            data.target.message("%s[UrbanDictionary]: Cache forcibly cleared." % (Escapes.LIGHT_BLUE))
            return
    
    def searchUD(self, term):
        
        requrl = self.url + "%s" % (
            urlencode(
                {
                    "term" : term
                }
            )
        )
        
        data = urlopen(requrl)
        data = json.loads(data.read())

        return data if data is not None else None
    
    def beginQuery(self, data, term):
    
        data.target.message("%s[UrbanDictionary]%s: %sSearching..." % (Escapes.BOLD, Escapes.BOLD, Escapes.AQUA))
        try:
            if term in self.cache:
                response = self.cache[term]
            elif term not in self.cache:
                response = self.searchUD(term)
                self.cache.update({
                    term : response
                })
            if response is None:
                data.target.message("%s[UrbanDictionary]%s: %s%s%s is not defined yet." % (Escapes.BOLD, Escapes.BOLD, Escapes.RED, term, Escapes.RED))
                return
            else:
                if response['result_type'] == 'no_response':
                    data.target.message("%s[UrbanDictionary]%s: %s%s%s is not defined yet." % (Escapes.BOLD, Escapes.BOLD, Escapes.RED, term, Escapes.RED))
                    return
                definitions = response['list'][0:4]
                if len(definitions) == 0:
                    data.target.message("%s[UrbanDictionary]%s: %s%s%s is not defined yet." % (Escapes.BOLD, Escapes.BOLD, Escapes.RED, term, Escapes.RED))
                    return                    
                try:
                    i = 1
                    for definition in definitions:
                        data.target.privmsg(" - %sDefinition #%s%s: " % (Escapes.BLUE, i, Escapes.BLUE))
                        for line in definition['definition'].splitlines():
                            if line.strip() == '':
                                continue
                            data.target.privmsg("  -> %s" % (line))
                        data.target.privmsg(" - %sExamples%s: " % (Escapes.GREEN, Escapes.GREEN))
                        for line in definition['example'].splitlines():
                            if line.strip() == '':
                                continue
                            data.target.privmsg("  -> %s" % (line))
                        i += 1
                except (UnicodeEncodeError, UnicodeDecodeError, LookupError) as e:
                    data.target.privmsg(" - %s%sCould not decode results.%s" % (Escapes.BOLD, Escapes.RED, Escapes.NL))
                    [self.log_error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]
                    return
        except: [self.log_error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]

__data__ = {
    'name'      : "UrbanDictionary",
    'version'   : "1.1",
    'require'   : ["IdentificationPlugin"],
    'main'      : UrbanDictionary,
    'events'    : []
}

__help__ = {
    '@ud'             : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Searches UrbanDictionary for a term.',
        PARAMS  : '<term>',
        ALIASES : ['urbandictionary']
    },
    '@ud-cache'       : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Displays the number of entries held in the cache.',
        PARAMS  : '',
        ALIASES : ['urbandictionary-cache']
    },
    '@ud-cache-clear' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Clears the cache forcibly before the scheduled time.',
        PARAMS  : '',
        ALIASES : ['urbandictionary-cacheclear']
    }
}
