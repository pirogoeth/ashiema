# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013-2015 Sean Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import ashiema, collections, imp, malibu, os, traceback

from imp import load_source

from ashiema.api.help import HelpFactory, Contexts
from ashiema.irc.eventhandler import EventHandler

from malibu.util.log import LoggingDriver


class PluginLoader(object):
    """ this manages loading and unloading of all plugins. """

    __instance = None

    @staticmethod
    def get_instance():

        if PluginLoader.__instance is None:
            return PluginLoader()
        else:
            return PluginLoader.__instance

    def __init__(self):

        PluginLoader.__instance = self

        # set up storage
        self.container = {}
        self.loaded = {}

        # set up objects
        self.helpfactory = HelpFactory.get_instance()

        # set up logging
        self.log = LoggingDriver.find_logger()

        self._loaded = False

        # plugin list and listing type
        self._list_type = (ashiema.config.get_section('plugins')
                           .get_string('list-type', 'blacklist').lower())
        self._list = (ashiema.config.get_section('plugins')
                      .get_string('list', '').split(',') or [])

    def __call__(self):

        return self.loaded

    def __getitem__(self, plugin):

        return self.loaded[plugin]

    def __depcheck__(self, container):

        try:
            for plugin, data in container.iteritems():
                for require in data['require']:
                    if require not in container:
                        msg = ('Plugin [%s] will not be loaded due to '
                               'dependency problems. Missing dep. [%s]' % (
                               plugin, require))
                        self.log.warning(msg)

                        _c = container
                        del _c[plugin]
                        self.__depcheck__(_c)
        except (RuntimeError): return {}
        return container

    def get_plugin(self, plugin):

        try: return self.loaded[plugin]
        except:
            [self.log.error(trace)
             for trace in traceback.format_exc(6).split('\n')]
            return None

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

            if self._list_type == 'blacklist' and source.__data__['name'] in self._list:
                self.log.info('Plugin [%s] is blacklisted, so it will not be loaded.' % (source.__data__['name']))
                continue
            elif self._list_type == 'whitelist' and source.__data__['name'] not in self._list:
                self.log.info('Plugin [%s] is not whitelisted, so it will not be loaded.' % (source.__data__['name']))
                continue

            self.container.update(
                {
                    source.__data__['name']:
                    {
                        'version': source.__data__['version'],
                        'require': source.__data__['require'],
                        'main': source.__data__['main'],
                        'events': (source.__data__['events'] or [])
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
        unload = []
        if self.container:
            # initialise events from plugins
            for data in self.container.values():
                for event in data['events']:
                    event()

            # initialise plugins
            for plugin, data in self.container.iteritems():
                try:
                    self.loaded.update(
                        {
                            plugin : data['main']()
                        }
                    )
                except:
                    self.log.info('an error has occurred in %s (%s):' % (plugin, data['version']))
                    [self.log.error(trace) for trace in traceback.format_exc(4).split('\n')]
                    unload.append(plugin)
                    continue

            if len(unload) > 0:
                self.log.info('some plugins have failed to load.')
                for plugin in unload:
                    self.container.pop(plugin)
                    self.log.error('%s failed to load and has been unloaded.' % (plugin))
            self.log.info('all plugins have been loaded.')

            # run the PluginsLoadedEvent
            EventHandler.get_instance().fire_once(EventHandler.get_instance().get_events()['PluginsLoadedEvent'], ())
        elif not self.container: self.log.info('no plugins to load.')

    def reload(self):

        # run the unload method
        self.unload()
        # recreate the containers
        self.loaded, self.container = ({}, {})
        # reload all plugins
        self.load()

    def unload(self):

        try:
            # this unloads all currently loaded plugins (eg., for shutdown)
            for name, plugin in self.loaded.iteritems():
                plugin.__deinit__()

            # clear status containers
            self.loaded.clear()
            self.container.clear()

            # delete containers
            del self.loaded, self.container
        except: pass
