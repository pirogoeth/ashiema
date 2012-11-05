#!/usr/bin/env python

import os, re, logging, core, urllib2, json, contextlib
from core import CorePlugin, Event, get_connection, util
from core.util import Escapes
from core.CorePlugin import Plugin
from contextlib import closing
from urllib2 import urlopen, HTTPError

class YoutubeScraper(Plugin):

    def __init__(self, connection, eventhandler):
    
        Plugin.__init__(self, connection, eventhandler, needs_dir = False)
        
        self.regexp = r"""(?:http://(?:www.|)youtube.com/(?:watch\?v=(\w*)))"""
        self.pattern = re.compile(self.regexp, re.VERBOSE)
        
        self.format = "[%sYou%sTube%s] %s&t%s - %s&a%s" % (Escapes.YELLOW, Escapes.RED, Escapes.BLACK, Escapes.AQUA, Escapes.BLACK, Escapes.GREY, Escapes.BLACK)
        self.apiurl = "http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=jsonc"
        
        self.eventhandler.get_default_events()['MessageEvent'].register(self.handler)
        
    def __deinit__(self):
    
        self.eventhandler.get_default_events()['MessageEvent'].deregister(self.handler)
    
    def get_simple_time(self, duration):
    
        return str(int(duration)) + "s"
        
    def handler(self, data):
     
        if len(self.pattern.findall(data.message.to_s())) >= 1:
            for id in self.pattern.findall(data.message.to_s()):
                try:
                    with closing(urlopen(self.apiurl % (id))) as req:
                        info = json.loads(req.read(), encoding = 'utf-8')
                        data.target.message(self.format.replace("&t", info['data']['title']).replace("&a", info['data']['uploader']))
                except (HTTPError, IOError) as e:
                    data.target.message("[%sYou%sTube%s] Invalid video link!" % (Escapes.YELLOW, Escapes.RED, Escapes.BLACK))


__data__ = {
    'name'     : "YoutubeScraper",
    'version'  : "1.0",
    'require'  : [],
    'main'     : YoutubeScraper
}