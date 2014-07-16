#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, logging, ashiema, sys, traceback, re, json
from ashiema import Plugin, Events, util
from ashiema.util import Escapes, unescape, fix_unicode
from ashiema.Plugin import Plugin
from ashiema.HelpFactory import Contexts, CONTEXT, PARAMS, DESC, ALIASES
from urllib import urlopen, urlencode

class GoogleSearch(Plugin):
    
    def __init__(self):
    
        Plugin.__init__(self, needs_dir = False)
        
        self.cache = {}
        
        self.get_event("MessageEvent").register(self.handler)
        self.get_event("PMEvent").register(self.handler)
        
        self.connection.tasks.update({
            "GoogleSearch__scheduled_cache_clean" :
                self.scheduler.add_interval_job(
                    self.clean_cache,
                    days = 1
                )
            }
        )
        
        self.url = "https://ajax.googleapis.com/ajax/services/search/web?"
        self.prefix = "%sG%so%so%sg%sl%se%s" % (Escapes.BLUE, Escapes.RED, Escapes.YELLOW, Escapes.BLUE, Escapes.GREEN, Escapes.RED, Escapes.COLOURED)
        
    def __deinit__(self):
    
        self.get_event("MessageEvent").deregister(self.handler)
        self.get_event("PMEvent").deregister(self.handler)
        
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
                try:
                    data.respond_to_user("[" + self.prefix + "Search]: %s%s%s, %s" % (Escapes.BOLD, title, Escapes.BOLD, url))
                    return
                except (UnicodeEncodeError):
                    data.respond_to_user("[" + self.prefix + "Search]: %sIncomplete Search%s, %s" % (Escapes.BOLD, Escapes.BOLD, url))
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