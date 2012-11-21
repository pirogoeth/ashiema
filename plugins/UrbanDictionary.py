#!/usr/bin/env python

import os, logging, core, sys, traceback, re, json
from core import CorePlugin, Event, get_connection, util
from core.util import Escapes as e
from core.CorePlugin import Plugin
from core.HelpFactory import Contexts
from core.HelpFactory import CONTEXT, PARAMS, DESC, ALIASES
from urllib import urlopen, urlencode

class UrbanDictionary(Plugin):

    def __init__(self, connection, eventhandler):
    
        Plugin.__init__(self, connection, eventhandler, needs_dir = False)
        
        self.cache = {}
        self.scheduler = connection.scheduler
        
        self.eventhandler.get_default_events()['MessageEvent'].register(self.handler)
        self.eventhandler.get_default_events()['PluginsLoadedEvent'].register(self._load_identification)
        
        self.connection.tasks.update({
            "UrbanDictionary__scheduled_cache_clean" :
                self.scheduler.add_interval_job(
                    self.clean_cache,
                    days = 1
                )
            }
        )
        
        self.url = "http://www.urbandictionary.com/tooltip.php?"
    
    def __deinit__(self):
    
        self.eventhandler.get_default_events()['MessageEvent'].deregister(self.handler)
        self.eventhandler.get_default_events()['PluginsLoadedEvent'].deregister(self._load_identification)
        
        self.scheduler.unschedule_job(
            self.connection.tasks["UrbanDictionary__scheduled_cache_clean"]
        )
        
        self.connection.tasks.pop(
            "UrbanDictionary__scheduled_cache_clean"
        )
    
    def _load_identification(self):
    
        self.identification = self.connection.pluginloader.get_plugin("IdentificationPlugin")
    
    def clean_cache(self):
    
        self.cache.clear()
    
    def handler(self, data):
    
        if data.message == (0, "@ud") or data.message == (0, "urbandictionary"):
            try:
                term = " ".join(data.message[1:])
            except (IndexError):
                data.target.message("%s[UrbanDictionary]: %sPlease provide a term to search for." % (e.AQUA, e.BOLD))
                return
            self.beginQuery(data, term)
        elif data.message == (0, "@ud-cache") or data.message == (0, "urbandictionary-cache"):
            assert self.identification.require_level(data, 1)
            data.target.message("%s[UrbanDictionary]: %s objects cached." % (e.AQUA, len(self.cache)))
            return
        elif data.message == (0, "@ud-cache-clear") or data.message == (0, "urbandictionary-clearcache"):
            assert self.identification.require_level(data, 1)
            self.clean_cache()
            data.target.message("%s[UrbanDictionary]: Cache forcibly cleared." % (e.LIGHT_BLUE))
            return
    
    def searchUD(self, term):
        
        _data = urlopen(self.url + "%s" % (
            urlencode(
                {
                    "term" : term
                }
            )
        ))
        _data = u'%s' % (_data.read().replace('\n', '\\n'))
        _data = json.loads(_data)['string']
        content = re.compile(r"<div>(.+?)<\/div><div>(.+?)<\/div>")
        escapes = re.compile(r"[\r\n\t]")
        escaped = escapes.sub('', _data.replace("<br/>", '').replace('&quot;', '"').strip())
        try:
            _result = content.match(escaped).groups()
        except: 
            [logging.getLogger("ashiema").error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]
            result = None

        result = [slice for slice in _result]
        result[0] = result[0].replace("<b>", '').replace("</b>", '').strip()
        result[1] = result[1].lstrip()
        result[1] = result[1].replace("<b>", e.BOLD).replace("</b>", e.BOLD)

        return result if result is not None else None
    
    def beginQuery(self, data, term):
    
        data.target.message("%s[UrbanDictionary]%s: %sSearching..." % (e.BOLD, e.BOLD, e.AQUA))
        try:
             if term in self.cache:
                 response = self.cache[term]
             elif term not in self.cache:
                 response = self.searchUD(term)
                 self.cache.update({
                     term : response
                 })
             if response is None:
                 data.target.message("%s[UrbanDictionary]%s: %s%s%s is not defined yet." % (e.BOLD, e.BOLD, e.RED, term, e.RED))
                 return
             else:
                 _term, _definition = response
                 data.target.message(
                     "%s[UrbanDictionary]%s: Definition for %s%s%s:" % (e.BOLD, e.BOLD, e.BOLD, _term, e.BOLD),
                     "%s[UrbanDictionary]%s: %s%s%s" % (e.BOLD, e.BOLD, e.AQUA, _definition, e.AQUA)
                 )
                 return
        except: [logging.getLogger("ashiema").error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]

__data__ = {
    'name'      : "UrbanDictionary",
    'version'   : "1.0",
    'require'   : ["IdentificationPlugin"],
    'main'      : UrbanDictionary
}

__help__ = {
    '@ud'             : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Searches UrbanDictionary for a term.',
        PARAMS  : '<term>'
    },
    '@ud-cache'       : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Displays the number of entries held in the cache.',
        PARAMS  : ''
    },
    '@ud-cache-clear' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Clears the cache forcibly before the scheduled time.',
        PARAMS  : ''
    }
}
