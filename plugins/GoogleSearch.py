#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, logging, core, sys, traceback, re, json, htmlentitydefs
from core import Plugin, Event, get_connection, util
from core.util import Escapes, unescape
from core.Plugin import Plugin
from core.HelpFactory import Contexts, CONTEXT, PARAMS, DESC, ALIASES
from urllib import urlopen, urlencode

class GoogleSearch(Plugin):
    
    def __init__(self, connection, eventhandler):
    
        Plugin.__init__(self, connection, eventhandler, needs_dir = False)
        
        self.cache = {}
        self.scheduler = connection.scheduler
        
        self.eventhandler.get_events()['MessageEvent'].register(self.handler)
        self.eventhandler.get_events()['PMEvent'].register(self.handler)
        
        self.connection.tasks.update({
            "GoogleSearch__scheduled_cache_clean" :
                self.scheduler.add_interval_job(
                    self.clean_cache,
                    days = 1
                )
            }
        )
        
        self.url = "https://ajax.googleapis.com/ajax/services/search/web?"
        self.prefix = "%sG%so%so%sg%sl%se%s" % (Escapes.BLUE, Escapes.RED, Escapes.YELLOW, Escapes.BLUE, Escapes.GREEN, Escapes.RED, Escapes.BLACK)
        
    def __deinit__(self):
    
        self.eventhandler.get_events()['MessageEvent'].deregister(self.handler)
        self.eventhandler.get_events()['PMEvent'].deregister(self.handler)
        
        self.scheduler.unschedule_job(
            self.connection.tasks.pop("GoogleSearch__scheduled_cache_clean")
        )
    
    def clean_cache(self):
    
        self.cache.clear()
    
    def handler(self, data):
    
        if data.message == (0, '@google'):
            try: query = " ".join(data.message[1:])
            except (IndexError):
                data.respond_to_user("[" + self.prefix + "Search]: You must provide a term to search!")
                return
            if query in self.cache:
                if self.cache[query] == (None, None):
                    data.respond_to_user("[" + self.prefix + "Search]: No results could be found. Please refine your search terms.")
                    return
                title, url = self.cache[query]
                # display result
                data.respond_to_user("[" + self.prefix + "Search]: %s%s%s, %s" % (Escapes.BOLD, title, Escapes.BOLD, url))
                return
            data.respond_to_user("[" + self.prefix + "Search]: Searching...")
            target_url = self.url + "%s" % (
                urlencode(
                    {
                        "v" : "1.0",
                        "q" : query
                    }
                )
            )
            response = urlopen(target_url)
            response = json.loads(response.read())
            if response['responseStatus'] != 200:
                code = response['responseStatus']
                error = response['responseDetails']
                data.respond_to_user("[" + self.prefix + "Search]: An error occurred while searching!")
                data.respond_to_user("[" + self.prefix + "Search]: Failed with code [" + str(code) + "]: " + error)
                return
            try:
                title = unescape(response['responseData']['results'][0]['titleNoFormatting'])
                url = response['responseData']['results'][0]['url']
            except (Exception):
                self.cache[query] = (None, None)
                return self.handler(data)
            self.cache[query] = (title, url)
            # re-call myself, so that there's not as much duplicate code.
            return self.handler(data)

__data__ = {
    'name'      : 'GoogleSearch',
    'version'   : '1.0',
    'require'   : [],
    'main'      : GoogleSearch,
    'events'    : []
}

__help__ = {
    '@google' : {
        CONTEXT : Contexts.BOTH,
        DESC    : 'Performs a Google search and returns the highest ranking result.',
        PARAMS  : '<query>',
        ALIASES : []
    }
}