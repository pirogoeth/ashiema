#!/usr/bin/env python

import os, logging, core, sys, traceback, re
from core import CorePlugin, Event, get_connection, util
from core.util import Escapes as e
from core.CorePlugin import Plugin
from urllib import urlopen

class AutoMeme(Plugin):
    def __init__(self, connection, eventhandler):
    
        Plugin.__init__(self, connection, eventhandler)
        
        self.eventhandler.get_default_events()['MessageEvent'].register(self.handler)
        
        self.api_url = "http://api.autome.me/text?lines=1"
        
    def __deinit__(self):
    
        self.eventhandler.get_default_events()['MessageEvent'].deregister(self.handler)
    
    def _retrieve(self):
 
        meme = urlopen(self.api_url).read().strip('\n')
        return re.sub("_", e.BOLD, meme)
    
    def handler(self, data):
    
        if data.message == (0, "@meme") or data.message == (0, "MEMEGET!"):
            data.target.message("%s%s" % (e.LIGHT_BLUE, self._retrieve()))
            return

__data__ = {
    'name'      : "AutoMeme",
    'version'   : "1.0",
    'require'   : [],
    'main'      : AutoMeme
}
