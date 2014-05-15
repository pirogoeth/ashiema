#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import logging, util, os, errno, multiprocessing
from Connection import Connection
from EventHandler import EventHandler
from PluginLoader import PluginLoader
from util import Configuration
from util.Configuration import Configuration, ConfigurationSection

class Plugin(object):
    """ this is the plugin implementation. """
    
    def __init__(self, needs_dir = False, needs_comm_pipe = False):
        # you need to register events and commands and such right in here.
        
        self.connection = Connection.get_instance()
        self.eventhandler = EventHandler.get_instance()
        
        self.name = type(self).__name__
        self.path = os.getcwd() + "/plugins/" + self.name + "/"
        self.needs_dir = needs_dir

        self.scheduler = self.connection.get_scheduler()
        
        self.logger = logging.getLogger('ashiema')

        self.logger.debug("Initialising plugin: [" + self.name + "]")
        
        # set up the plugin's directory, if it doesn't exist.
        if not os.path.exists(self.path) and needs_dir:
            try:
                os.makedirs(self.path)
            except OSError as e:
                if exception.errno != errno.EEXIST:
                    raise
        
        # set up the comm pipe
        if needs_comm_pipe:
            self.__pipe = self.connection.get_send_pipe()
        else: 
            self.__pipe = None
    
    def __deinit__(self):
        # you need to deregister events and commands right here. this will be called by the plugin loader.
        
        pass
    
    def get_connection(self):
        """ returns the connection object. """
        
        return self.connection

    def get_configuration(self):
        """ returns the system configuration object. """

        return Configuration.get_instance()

    def get_plugin_configuration(self):
        """ returns the configuration dictionary from the system configuration for this
            specific plugin. """

        plugin_dict = self.get_configuration().get_section(self.name)
        return plugin_dict if plugin_dict is not None else ConfigurationSection()
    
    def get_eventhandler(self):
        """ returns the eventhandler object """
        
        return self.eventhandler
    
    def get_plugin(self, plugin):
        """ searches for +plugin+ in the plugin loader and returns it if available. """
        
        return PluginLoader.get_instance().get_plugin(plugin)
    
    def get_event(self, event):
        """ returns event +event+ if it exists or None. """
        
        try: return EventHandler.get_instance().get_event(event)
        except (IndexError) as e: return None

    def fire_event(self, event, data = None):
        """ fires +event+ """
        
        if event is not None:
            EventHandler.get_instance().fire_once(event, data)

    def get_path(self):
        """ returns the plugin directory path. """
        
        return self.path if self.needs_dir is True else ''
    
    def log_debug(self, *args):
        """ send data to the logger with level `debug`. """
        
        [self.logger.debug('[' + self.name + '] ' + message) for message in args]

    def log_info(self, *args):
        """ send data to the logger with level `info`. """
        
        [self.logger.info('[' + self.name + '] ' + message) for message in args]

    def log_warning(self, *args):
        """ send data to the logger with level `warning`. """
        
        [self.logger.warning('[' + self.name + '] ' + message) for message in args]

    def log_error(self, *args):
        """ send data to the logger with level `error`. """
        
        [self.logger.error('[' + self.name + '] ' + message) for message in args]

    def log_critical(self, *args):
        """ send data to the logger with level `critical`. """
        
        [self.logger.critical('[' + self.name + '] ' + message) for message in args]
    
    def allows_pipe(self):
        """ returns whether or not this plugin has comm pipe usage enabled """
        
        return self.__pipe is not None

    def push_data(self, *args):
        """ send data through the comm pipe, if it is enabled. """

        try: [self.__pipe.send(data) for data in args]
        except: return