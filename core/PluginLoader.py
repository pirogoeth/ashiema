#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import imp, util, os, logging, traceback, core
from imp import load_source
from core import get_connection, HelpFactory
from HelpFactory import HelpFactory, Contexts

class PluginLoader(object):
    """ this manages loading and unloading of all plugins. """
    
    def __init__(self, (connection, eventhandler)):
        # set up storage
        self.container = {}
        self.loaded = {}
        # set up objects
        self.connection = connection
        self.eventhandler = eventhandler
        self.helpfactory = HelpFactory()
        # set up logging
        self.log = logging.getLogger('ashiema')
        # assertion
        self._loaded = False
    
    def __call__(self):
        return self.loaded
    
    def __getitem__(self, plugin):
        return self()[plugin]
        
    """ support functions """
    def get_plugin(self, plugin):
        assert self._loaded is True, 'Plugins have not yet been loaded.'
        
        try: return self.loaded[plugin]
        except:
            [self.log.error(trace) for trace in traceback.format_exc(6).split('\n')]
            return None

    """ dependency support """
    def __depcheck__(self, container):
        try:
            for plugin, data in container.iteritems():
                for require in data['require']:
                    if require not in container:
                        self.log.warning('plugin [%s] will not be loaded due to dependency problems. missing dep [%s]' % (plugin, require))
                        _c = container
                        del _c[plugin]
                        self.__depcheck__(_c)
        except (RuntimeError): return {}
        return container
    
    """ load, reload, unload """
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
            try: source = load_source(plugin.split('.')[0], plugin_dir + plugin)
            except:
                self.log.info('an error has occurred while loading plugins.')
                [self.log.error(trace) for trace in traceback.format_exc(4).split('\n')]
                continue
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
            # load the help, if it's there.
            if hasattr(source, '__help__'):
                self.helpfactory.register(source.__data__['name'], source.__help__)
        # check requires
        self.container = self.__depcheck__(self.container)    
        """ setting the loading variable here makes dependency requires work correctly, and at this point, all plugins
            are effectively loaded, but they are just not yet initialised. """
        self._loaded = True
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
                    continue
            self.log.info('all plugins have been loaded.')
            # run the PluginsLoadedEvent
            get_connection()._evh.get_default_events()['PluginsLoadedEvent'].run()
        elif not self.container: self.log.info('no plugins to load.')
    
    def reload(self):
        assert self._loaded is True, 'Plugins have not yet been loaded.'
        
        # run the unload method
        self.unload()
        # recreate the containers
        self.loaded, self.container = ({}, {})
        # reload all plugins
        self.load()
    
    def unload(self):
        assert self._loaded is True, 'Plugins have not yet been loaded.'
        
        # this unloads all currently loaded plugins (eg., for shutdown)
        for name, plugin in self.loaded.iteritems():
            plugin.__deinit__()
        # clear status containers
        self.loaded.clear()
        self.container.clear()
        # delete containers
        del self.loaded, self.container