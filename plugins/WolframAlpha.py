#!/usr/bin/env python

import os, logging, core
from core import CorePlugin, Event, get_connection, util
from core.util import Escapes as e
from core.CorePlugin import Plugin
from urllib import urlopen, urlencode
import xml.etree.cElementTree as xtree
import sys, traceback

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
   
    def clean_cache(self):
       
        self.cache.clear()
   
    def handler(self, data):
       
        if data.message == (0, "@wa") or data.message == (0, "wolfram"):
            try:
                query = " ".join(data.message[1:])
            except (IndexError):
                data.target.message("%s[Wolfram|Alpha]: %sPlease provide a query to search." % (e.LIGHT_BLUE, e.BOLD))
                return
            self.beginWolframQuery(data, query)
        elif data.message == (0, "@wa-cache") or data.message == (0, "wolfram-cache"):
            assert self.identification.require_level(data, 1)
            data.target.message("%s[Wolfram|Cache]: %s objects cached." % (e.LIGHT_BLUE, len(self.cache)))
            return
        elif data.message == (0, "@wa-cache-clear") or data.message == (0, "wolfram-clearcache"):
            assert self.identification.require_level(data, 2)
            self.clean_cache()
            data.target.message("%s[Wolfram|Cache]: cache forcibly cleared." % (e.LIGHT_BLUE))
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
        ), _referrer = _referrer)
       
    def parseWolframResponse(self, response, redirected = False, results = None):
       
        results = results if results is not None else []
        tree = xtree.fromstring(response.read())
        recalculate = tree.get('recalculate') if tree.get('recalculate') else False
        success = tree.get('success')
        if success == 'true':
            for pod in tree.findall('pod'):
                title = pod.get('title')
                plaintext = pod.find('subpod/plaintext')
                if plaintext is not None and plaintext.text:
                    results.append((title, plaintext.text.split('\n')))
            if recalculate is not False:
                if not redirected:
                    return self.parseWolframResponse(urlopen(recalculate), redirected = True, results = results)
                elif results:
                    return True, results
                else:
                    return False, "Too many redirects."
            elif success == 'true' and recalculate is False and results is not None:
                return True, results
        else:
            return False, [tip.get("text") for tip in tree.findall("tips/tip")]
            
    def beginWolframQuery(self, data, query):    
        data.target.privmsg("%s[Wolfram|Alpha]%s: %sSearching..." % (e.BOLD, e.BOLD, e.LIGHT_BLUE))
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
                for title, pod in response:
                    try:
                        data.target.privmsg("%s%s%s%s" % (e.BOLD, title, e.BOLD, e.NL))
                        data.target.privmsg(" - %s%s%s" % (e.LIGHT_BLUE, " ".join(pod).encode("utf-8"), e.NL))
                    except (UnicodeEncodeError, LookupError) as er:
                        data.target.privmsg(" - %s%sUnicodeEncodeError: %s%s" % (e.BOLD, e.RED, er, e.NL))
                        pass
            elif not have_results:
                if len(response) == 0:
                    data.target.privmsg(" - %s%sNo results found, try a different keyword.%s" % (e.BOLD, e.RED, e.NL))
                elif len(response) != 0:
                    data.target.privmsg(" - %s%sNo results found, try a different keyword.%s%s%s%s" % (e.BOLD, e.RED, e.NL, e.BOLD, e.RED, response))
        except (TypeError, AttributeError, IOError) as er:
            # a wild exception appears.
            [logging.getLogger("ashiema").error("%s" % (tb)) for tb in traceback.format_exc(4).split('\n')]
            return
        except (IndexError) as e:
            data.target.message("%s[Wolfram|Alpha]: %sPlease provide a query to search." % (e.LIGHT_BLUE, e.BOLD))
            return
        except: raise

__data__ = {
    'name'    : "Wolfram|Alpha",
    'version' : "1.0",
    'require' : ["IdentificationPlugin"],
    'main'    : WolframAlpha
}

__help__ = {
    '@wa'             : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Searches Wolfram|Alpha for a query.',
        PARAMS  : '<query>'
    },
    '@wa-cache'       : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Displays the number of entries held in the cache.',
        PARAMS  : ''
    },
    '@wa-cache-clear' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Clears the cache forcibly before the scheduled time.',
        PARAMS  : ''
    }
}