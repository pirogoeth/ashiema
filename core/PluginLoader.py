#!/usr/bin/env python

import imp, util, os, logging, traceback
from imp import load_source

class PluginLoader(object):
    """ this manages loading and unloading of all plugins. """
    
    def __init__(self, (connection, eventhandler)):
        # set up storage
        self.container = {}
        self.loaded = {}
        # set up objects
        self.connection = connection
        self.eventhandler = eventhandler
        # set up logging
        self.log = logging.getLogger('ashiema')
    
    def load(self):
        # this loads all plugins
        plugin_dir = os.getcwd() + '/plugins/'
        files = os.listdir(plugin_dir)
        plugins = []
        # find plugin files
        for file in files:
            if file[-3:] == ".py":
                plugins.append(file)
        # update container with plugin information
        for plugin in plugins:
            source = load_source(plugin.split('.')[0], plugin_dir + plugin)
            self.container.update(
                {
                    source.__data__['name']:
                    {
                        'version': source.__data__['version'],
                        'main': source.__data__['main']
                    }
                }
            )
        # initialise plugins
        for plugin, data in self.container.iteritems():
            try:
                self.loaded.update(
                    {
                        name : data['main']((self.connection, self.eventhandler))
                    }
                )
            except:
                self.log.info('an error has occurred in %s (%s):' % (plugin, data['version']))
                [self.log.error(trace) for trace in traceback.format_exc(4)]
        self.log.info('all plugins have been loaded.')
    
    def reload(self):
        # this reloads all plugins and looks for new ones.
        for name, plugin in self.loaded.iteritems():
            plugin.__deinit__()
        # clear the status containers
        self.loaded.clear()
        self.container.clear()
        # reload all plugins
        self.load()
    
    def unload(self):
        # this unloads all currently loaded plugins (eg., for shutdown)
        for name, plugin in self.loaded.iteritems():
            plugin.__deinit__()
        # clear status containers
        self.loaded.clear()
        self.container.clear()
        # delete containers
        del self.loaded, self.container