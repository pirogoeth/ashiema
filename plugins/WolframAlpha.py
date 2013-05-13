#!/usr/bin/env python
# -*- coding: latin-1 -*-

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, logging, core
from core import Plugin, Event, get_connection, util
from core.util import Escapes
from core.Plugin import Plugin
from core.HelpFactory import Contexts
from core.HelpFactory import CONTEXT, DESC, PARAMS, ALIASES
from core.util.texttable import TextTable
from urllib import urlopen, urlencode
import xml.etree.cElementTree as xtree
import sys, traceback

from contextlib import closing

class WolframAlpha(Plugin):

    def __init__(self, connection, eventhandler):
        
        Plugin.__init__(self, connection, eventhandler, needs_dir = False)
    
        self.cache = {}
        self.scheduler = connection.scheduler
    
        self.eventhandler.get_default_events()['MessageEvent'].register(self.handler)
        self.eventhandler.get_default_events()['PluginsLoadedEvent'].register(self._load_identification)
    
        self.connection.tasks.update({
            "WolframAlpha__scheduled_cache_clean":
                self.scheduler.add_interval_job(
                    self.clean_cache,
                    days = 1
                )
            }
        )
        
        self.appID = "395X7T-8JLXGEP8YH"
    
    def __deinit__(self):
        
        self.eventhandler.get_default_events()['MessageEvent'].deregister(self.handler)
        self.eventhandler.get_default_events()['PluginsLoadedEvent'].deregister(self._load_identification)
        
        self.scheduler.unschedule_job(
            self.connection.tasks["WolframAlpha__scheduled_cache_clean"]
        )
        
        self.connection.tasks.pop(
            "WolframAlpha__scheduled_cache_clean"
        )
    
    def _load_identification(self):
       
        self.identification = self.connection.pluginloader.get_plugin("IdentificationPlugin")
    
    def _process_result_block_(self, data):
    
        data = data.strip('| ')
        data = data.decode('UTF-8', 'ignore')
        data = data.encode('UTF-8')
        return data
   
    def clean_cache(self):
       
        self.cache.clear()
   
    def handler(self, data):
       
        if data.message == (0, "@wa") or data.message == (0, "wolfram"):
            try:
                if len(data.message[1:]) > 1:
                    query = " ".join(data.message[1:])
                else:
                    query = data.message[1]
            except (IndexError) as e:
                data.target.message("%s[Wolfram|Alpha]: %sPlease provide a query to search." % (Escapes.LIGHT_BLUE, Escapes.BOLD))
                return
            self.beginWolframQuery(data, query)
        elif data.message == (0, "@wa-cache") or data.message == (0, "wolfram-cache"):
            assert self.identification.require_level(data, 1)
            data.target.message("%s[Wolfram|Cache]: %s objects cached." % (Escapes.LIGHT_BLUE, len(self.cache)))
            return
        elif data.message == (0, "@wa-cache-clear") or data.message == (0, "wolfram-cacheclear"):
            assert self.identification.require_level(data, 2)
            self.clean_cache()
            data.target.message("%s[Wolfram|Cache]: Cache forcibly cleared." % (Escapes.LIGHT_BLUE))
            return
   
    def search(self, query, format = ('plaintext',)):
       
        return self.parseWolframResponse(urlopen(
            "http://api.wolframalpha.com/v2/query?%s" % (
                urlencode(
                    {
                        "appid"  : self.appID,
                        "input"  : query,
                        "format" : ",".join(format)
                    }
                )
            )
        ))
       
    def parseWolframResponse(self, response, redirected = False, results = None, sources = None):
       
        results = results if results is not None else []
        sources = sources if sources is not None else []
        tree = xtree.fromstring(response.read())
        recalculate = tree.get('recalculate') if tree.get('recalculate') else False
        success = tree.get('success')
        if success == 'true':
            for pod in tree.findall('pod'):
                title = pod.get('title')
                plaintext = pod.find('subpod/plaintext')
                if plaintext is not None and plaintext.text:
                    try: results.append([title, [self._process_result_block_(text) for text in plaintext.text.split('\n')]])
                    except (UnicodeEncodeError, UnicodeDecodeError, LookupError) as e: continue
            if recalculate is not False:
                if not redirected:
                    return self.parseWolframResponse(urlopen(recalculate), redirected = True, results = results, sources = sources)
                elif results:
                    return True, results
                else:
                    return False, "Too many redirects."
            elif success == 'true' and recalculate is False and results is not None:
                return True, results
        else:
            return False, [tip.get("text") for tip in tree.findall("tips/tip")]
            
    def beginWolframQuery(self, data, query):    
        data.target.privmsg("%s[Wolfram|Alpha]%s: %sSearching..." % (Escapes.BOLD, Escapes.BOLD, Escapes.LIGHT_BLUE))
        try:
            if query in self.cache:
                response = self.cache[query]
                have_results = True
            elif query not in self.cache:
                result = self.search(query)
                have_results, response = result
                self.cache.update({
                    query: response
                })
            if have_results:
                # process resulsts
                header_pod = response.pop(0)
                result_tables = [TextTable() for pod in response]
                pod_data = [pod[1] for pod in response]
                print result_tables
                print header_pod
                print response
                result_tables[0].header = header_pod[1][0].title()
                i = 0
                while i < len(result_tables):
                    table = result_tables[i]
                    table.add_col_names([response[i][0]])
                    for item in response[i][1]:
                        table.add_row([item])
                    i += 1
                try:
                    data.target.privmsg("    ")
                    for table in result_tables:
                        for line in str(table).split('\n'):
                            data.target.privmsg(line)
                        data.target.privmsg("    ")
                except (UnicodeEncodeError, UnicodeDecodeError, LookupError) as e:
                    data.target.privmsg(" - %s%sCould not decode results.%s" % (Escapes.BOLD, Escapes.RED, Escapes.NL))
                    [logging.getLogger("ashiema").error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]
                    return
            elif not have_results:
                if len(response) == 0:
                    data.target.privmsg(" - %s%sNo results found, try a different keyword.%s" % (Escapes.BOLD, Escapes.RED, Escapes.NL))
                elif len(response) != 0:
                    data.target.privmsg(" - %s%sNo results found, try a different keyword.%s%s%s%s" % (Escapes.BOLD, Escapes.RED, Escapes.NL, Escapes.BOLD, Escapes.RED, response))
        except (TypeError, AttributeError, IOError) as er:
            # a wild exception appears.
            [logging.getLogger("ashiema").error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]
            return
        except (IndexError) as e:
            data.target.message("%s[Wolfram|Alpha]: %sError parsing results." % (Escapes.LIGHT_BLUE, Escapes.BOLD))
            [logging.getLogger("ashiema").error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]
            return
        except: raise

__data__ = {
    'name'    : "Wolfram|Alpha",
    'version' : "1.0",
    'require' : ["IdentificationPlugin"],
    'main'    : WolframAlpha,
    'events'  : []
}

__help__ = {
    '@wa'             : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Searches Wolfram|Alpha for a query.',
        PARAMS  : '<query>',
        ALIASES : ['wolfram']
    },
    '@wa-cache'       : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Displays the number of entries held in the cache.',
        PARAMS  : '',
        ALIASES : ['wolfram-cache']
    },
    '@wa-cache-clear' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Clears the cache forcibly before the scheduled time.',
        PARAMS  : '',
        ALIASES : ['wolfram-cacheclear']
    }
}