#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import ashiema, logging
from ashiema import Plugin
from ashiema.Plugin import Plugin

class ExamplePlugin(Plugin):

    def __init__(self):
        Plugin.__init__(self, needs_dir = False)
        
        self.get_event("MessageEvent").register(self.handler)
        
    def __deinit__(self):
        self.get_event("MessageEvent").deregister(self.handler)
        
    def handler(self, data):
        if data.message == (0, 'testing'):
            data.target.privmsg('this works bro.')

__data__ = {
    'name'     : 'ExamplePlugin',
    'version'  : '1.0',
    'require'  : [],
    'main'     : ExamplePlugin,
    'events'   : []
}