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
    
    def __depcheck__(self, container):
        try:
            for plugin, data in container.iteritems():
                for require in data['require']:
                    if require not in container:
                        self.log.warning('plugin [%s] will not be loaded due to dependency problems. missing dep [%s]')
                        _c = container
                        del _c[plugin]
                        self.__depcheck__(_c)
        except (RuntimeError): return {}
        return container
    
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
            if not hasattr(source, '__data__'): continue
            self.container.update(
                {
                    source.__data__['name']:
                    {
                        'version': source.__data__['version'],
                        'require': source.__data__['require'],
                        'main': source.__data__['main']
                    }
                }
            )
        # check requires
        self.container = self.__depcheck__(self.container)    
        # initialise plugins
        if self.container:
            for plugin, data in self.container.iteritems():
                try:
                    self.loaded.update(
                        {
                            plugin : data['main'](self.connection, self.eventhandler)
                        }
                    )
                except:
                    self.log.info('an error has occurred in %s (%s):' % (plugin, data['version']))
                    [self.log.error(trace) for trace in traceback.format_exc(4).split('\n')]
            self.log.info('all plugins have been loaded.')
        elif not self.container: self.log.info('no plugins to load.')
    
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