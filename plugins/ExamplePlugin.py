#!/usr/bin/env python

import core, logging
from core import CorePlugin
from core.CorePlugin import Plugin

class ExamplePlugin(Plugin):
    def __init__(self, connection, eventhandler):
        Plugin.__init__(self, connection, eventhandler)
        
        self.eventhandler.get_default_events()['MessageEvent'].register(self.handler)
        
        logging.getLogger('ashiema').info('ExamplePlugin has been loaded.')
    
    def __deinit__(self):
        self.eventhandler.get_default_events()['MessageEvent'].deregister(self.handler)
        
        logging.getLogger('ashiema').info('ExamplePlugin has been unloaded.')
    
    def handler(self, data):
        if data.message == (0, 'testing'):
            data.target.privmsg('this works bro.')

__data__ = {
    'name'     : 'ExamplePlugin',
    'version'  : '1.0',
    'require'  : [],
    'main'     : ExamplePlugin
}