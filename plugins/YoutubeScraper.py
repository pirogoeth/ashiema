#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, re, logging, ashiema, urllib2, json, contextlib
from ashiema import Plugin, Events, util
from ashiema.util import Escapes
from ashiema.Plugin import Plugin
from contextlib import closing
from urllib2 import urlopen, HTTPError

class YoutubeScraper(Plugin):

    def __init__(self):
    
        Plugin.__init__(self, needs_dir = False)
        
        self.regexp = r"""(?:https?://(?:www.|)youtube.com/(?:watch\?v=([\w-]+)))|(?:https?://youtu.be/([\w-]+))"""
        self.pattern = re.compile(self.regexp, re.VERBOSE)
        
        self.format = "[%sYou%sTube%s] %s&t%s [&d] - %s&a%s" % (Escapes.YELLOW, Escapes.RED, Escapes.BLACK, Escapes.AQUA, Escapes.BLACK, Escapes.GREY, Escapes.BLACK)
        self.apiurl = "http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=jsonc"
        
        self.get_event("MessageEvent").register(self.handler)
        
    def __deinit__(self):
    
        self.get_event("MessageEvent").deregister(self.handler)
    
    def get_strtime(self, duration):
    
        day, hr, min, sec = (None, None, None, None)
        
        if duration >= 60:
            sec = duration % 60
            min = duration / 60
        else:
            sec = duration
        
        if min >= 60:
            hr = (min / 60)
            min = min - (60 * hr)
        
        if hr >= 24:
            day = (hr / 24)
            hr = hr - (hr * 24)
        
        timestr = ""

        if day:
            if day > 1:
                timestr += "%s days, " % (day)
            else:
                timestr += "%s day, " % (day)
        
        if hr:
            if hr > 1:
                timestr += "%s hours, " % (hr)
            else:
                timestr += "%s hour, " % (hr)
        
        if min:
            if min > 1:
                timestr += "%s minutes, " % (min)
            else:
                timestr += "%s minute, " % (min)

        if sec:
            if sec > 1:
                timestr += "%s seconds" % (sec)
            else:
                timestr += "%s second" % (sec)
        
        return timestr
        
    def handler(self, data):
     
        if len(self.pattern.findall(data.message.to_s())) >= 1:
            for vid in self.pattern.findall(data.message.to_s())[0]:
                if vid == '' or vid is None: continue
                try:
                    with closing(urlopen(self.apiurl % (vid))) as req:
                        info = json.loads(req.read(), encoding = 'utf-8')
                        timestr = self.get_strtime(int(info['data']['duration']))
                        data.target.message(self.format.replace("&t", info['data']['title']).replace("&a", info['data']['uploader']).replace("&d", timestr))
                except (HTTPError, IOError) as e:
                    data.target.message("[%sYou%sTube%s] Invalid video link!" % (Escapes.YELLOW, Escapes.RED, Escapes.BLACK))


__data__ = {
    'name'     : "YoutubeScraper",
    'version'  : "1.0",
    'require'  : [],
    'main'     : YoutubeScraper,
    'events'   : []
}