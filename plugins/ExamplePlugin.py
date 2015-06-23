# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013-2015 Sean Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import ashiema, malibu

from ashiema.api.events import Event
from ashiema.api.help import Contexts, CONTEXT, DESC, PARAMS, ALIASES
from ashiema.api.plugin import Plugin
from ashiema.util import Escapes

from malibu.util.log import LoggingDriver


class ExamplePlugin(Plugin):

    def __init__(self):
        
        Plugin.__init__(self, needs_dir = False, needs_comm_pipe = False)
        
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

__help__ = {
    'testing' : {
        CONTEXT    : Contexts.PUBLIC,
        DESC       : "Just a test.",
        ALIASES    : [],
        PARAMS     : ''
    }
}
