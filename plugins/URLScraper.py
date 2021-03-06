#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, re, logging, ashiema, urllib2, json, contextlib, traceback
from ashiema import Plugin, Events, util
from ashiema.util import Escapes, unescape
from ashiema.Plugin import Plugin
from contextlib import closing
from urllib2 import urlopen, HTTPError

class URLScraper(Plugin):

    def __init__(self):
    
        Plugin.__init__(self, needs_dir = False)
        
        # props to John Gruber, http://daringfireball.net/2010/07/improved_regex_for_matching_urls
        self.regexp = r"""(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'"\.<>]))"""
        self.title_regexp = r"""<title>(.*?)</title>"""
        self.pattern = re.compile(self.regexp, re.VERBOSE)
        self.title_pattern = re.compile(self.title_regexp, re.VERBOSE | re.DOTALL | re.M)
        
        self.alt_title_len = 50
        
        self.format = "[%sURLScraper%s] %s^t^%s - [%s^l^%s]" % (Escapes.GREEN, Escapes.BLACK, Escapes.AQUA, Escapes.BLACK, Escapes.GREY, Escapes.BLACK)
        
        self.get_event("MessageEvent").register(self.handler)
        
    def __deinit__(self):
    
        self.get_event("MessageEvent").deregister(self.handler)
    
    def get_simple_time(self, duration):
    
        return str(int(duration)) + "s"
        
    def handler(self, data):
     
        if len(self.pattern.findall(data.message.to_s())) >= 1:
            for link in self.pattern.findall(data.message.to_s()):
                link = link[0]
                try:
                    with closing(urlopen(link)) as req:
                        if req.info().getmaintype() != 'text':
                            return
                        content = req.read()
                        if len(self.title_pattern.findall(content)) >= 1:
                            title = self.title_pattern.findall(content)[0]
                        else:
                            title = '"' + content[:self.alt_title_len] + '..."'
                        try:
                            data.target.message(self.format.replace("^t^", unescape(title)).replace("^l^", req.geturl()))
                        except (UnicodeDecodeError) as e:
                            data.target.message("[%sURLScraper%s] %sCould not decode title information!%s" % (Escapes.GREEN, Escapes.BLACK, Escapes.AQUA, Escapes.BLACK))
                except (HTTPError) as e:
                    data.target.message("[%sURLScraper%s] %sCould not fetch title information!%s [%s%s%s - %s%s%s]" % (Escapes.GREEN, Escapes.BLACK, Escapes.AQUA, Escapes.BLACK, Escapes.RED, e.code, Escapes.BLACK, Escapes.GREY, str(e.reason), Escapes.BLACK))
                except (IOError) as e:
                    data.target.message("[%sURLScraper%s] %sCould not fetch title information!%s" % (Escapes.GREEN, Escapes.BLACK, Escapes.AQUA, Escapes.BLACK))

__data__ = {
    'name'     : "URLScraper",
    'version'  : "1.0",
    'require'  : [],
    'main'     : URLScraper,
    'events'   : []
}