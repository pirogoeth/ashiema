#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import logging, util, os, errno

class Plugin(object):
    """ this is the plugin implementation. """
    
    def __init__(self, connection, eventhandler, needs_dir = False):
        # you need to register events and commands and such right in here.
        
        self.connection = connection
        self.eventhandler = eventhandler
        
        self.name = type(self).__name__
        self.path = os.getcwd() + "/plugins/" + self.name + "/"
        self.needs_dir = needs_dir

        logging.getLogger('ashiema').debug("Initialising plugin: [" + self.name + "]")
        
        # set up the plugins directory, if it doesn't exist.
        if not os.path.exists(self.path) and needs_dir:
            try:
                os.makedirs(self.path)
            except OSError as e:
                if exception.errno != errno.EEXIST:
                    raise
    
    def __deinit__(self):
        # you need to deregister events and commands right here. this will be called by the plugin loader.
        
        pass
    
    def get_connection(self):
        """ returns the connection object. """
        
        return self.connection

    def get_configuration(self):
        """ returns the system configuration object. """

        return self.connection.configuration

    def get_plugin_configuration(self):
        """ returns the configuration dictionary from the system configuration for this
            specific plugin. """

        plugin_dict = self.get_configuration().get_category(self.name)
        return plugin_dict if plugin_dict is not None else {}
    
    def get_eventhandler(self):
        """ returns the eventhandler object """
        
        return self.eventhandler
    
    def get_plugin(self, plugin):
        """ searches for +plugin+ in the plugin loader and returns it if available. """
        
        return self.connection.pluginloader.get_plugin(plugin)
    
    def get_path(self):
        """ returns the plugin directory path. """
        
        return self.path if self.needs_dir is True else ''