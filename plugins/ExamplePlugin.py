#!/usr/bin/env python

import core, logging
from core import Plugin

class ExamplePlugin(Plugin.Plugin):
    def __init__(self, connection, eventhandler):
        Plugin.__init__(self, connection, eventhandler)
        
        self.eventhandler.get_default_events()['MessageEvent'].register(self.handler)
        
        logging.getLogger('ashiema').info('ExamplePlugin has been loaded.')
    
    def __deinit__(self):
        self.eventhandler.get_default_events()['MessageEvent'].deregister(self.handler)
        
        logging.getLogger('ashiema').info('ExamplePlugin has been loaded.')
    
    def handler(self, data):
        logging.getLogger('ashiema').info('handling message: %s' % (data.message))

__data__ = {
    'name'     : 'ExamplePlugin',
    'version'  : '1.0',
    'main'     : ExamplePlugin
}