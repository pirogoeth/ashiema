#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, re, logging, core, urllib2, json, contextlib
from core import Plugin, Events, util
from core.util import Escapes
from core.Plugin import Plugin
from contextlib import closing
from urllib2 import urlopen, HTTPError

class YoutubeScraper(Plugin):

    def __init__(self):
    
        Plugin.__init__(self, needs_dir = False)
        
        self.regexp = r"""(?:https?://(?:www.|)youtube.com/(?:watch\?v=([\w-]+)))|(?:https?://youtu.be/([\w-]+))"""
        self.pattern = re.compile(self.regexp, re.VERBOSE)
        
        self.format = "[%sYou%sTube%s] %s&t%s [&d minutes] - %s&a%s" % (Escapes.YELLOW, Escapes.RED, Escapes.BLACK, Escapes.AQUA, Escapes.BLACK, Escapes.GREY, Escapes.BLACK)
        self.apiurl = "http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=jsonc"
        
        self.get_event("MessageEvent").register(self.handler)
        
    def __deinit__(self):
    
        self.get_event("MessageEvent").deregister(self.handler)
    
    def get_simple_time(self, duration):
    
        return str(int(duration)) + "s"
        
    def handler(self, data):
     
        if len(self.pattern.findall(data.message.to_s())) >= 1:
            for vid in self.pattern.findall(data.message.to_s())[0]:
                if vid == '' or vid is None: continue
                try:
                    with closing(urlopen(self.apiurl % (vid))) as req:
                        info = json.loads(req.read(), encoding = 'utf-8')
                        data.target.message(self.format.replace("&t", info['data']['title']).replace("&a", info['data']['uploader']).replace("&d", str(int(info['data']['duration']) / 60)))
                except (HTTPError, IOError) as e:
                    data.target.message("[%sYou%sTube%s] Invalid video link!" % (Escapes.YELLOW, Escapes.RED, Escapes.BLACK))


__data__ = {
    'name'     : "YoutubeScraper",
    'version'  : "1.0",
    'require'  : [],
    'main'     : YoutubeScraper,
    'events'   : []
}