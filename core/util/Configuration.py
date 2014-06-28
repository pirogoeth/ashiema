#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import copy

class ConfigurationSection(dict):
    """ modified dictionary that returns none for invalid keys """
    
    def __init__(self):
        dict.__init__(self)
        
        self.mutable = True
    
    def __getitem__(self, key):
    
        try: return dict.__getitem__(self, key)
        except (IndexError, KeyError) as e:
            raise KeyError("Unknown configuration key '%s'." % (key))
    
    def __setitem__(self, key, value):
    
        if self.mutable:
            self.update({ key: value })
        else:
            raise AttributeError("This section is not mutable.")
    
    def set_mutable(self, mutable):
    
        self.mutable = mutable
    
    def set(self, key, value):
    
        return self.__setitem__(key, value)
    
    def get(self, key):
    
        return self.__getitem__(key)
    
    def get_list(self, key, delimiter = ",", default = []):
    
        try:
            val = self.get(key)
            return val.split(delimiter) if len(val) > 0 else default
        except: return default                

    def get_string(self, key, default = ""):
    
        try: return str(self.get(key)) or default
        except: return default
    
    def get_int(self, key, default = None):
    
        try: return int(self.get(key)) or default
        except: return default
    
    def get_bool(self, key, default = False):
    
        try:
            val = self.get(key) or default
            if isinstance(val, bool):
                return val
            elif isinstance(val, str):
                if val.lower() == 'true':
                    self.set(key, True)
                    return True
                elif val.lower() == 'false':
                    self.set(key, False)
                    return False
                else:
                    return default
            elif isinstanct(val, int):
                if val == 1:
                    self.set(key, True)
                    return True
                elif val == 0:
                    self.set(key, False)
                    return False
                else:
                    return default
            else:
                return default
        except: return default

class Configuration(object):
    """ this will hold the configuration.
        it will not actually read the configuration itself, but it
        will carry everything """
    
    __instance = None
    
    @staticmethod
    def get_instance():

        return Configuration.__instance

    def __init__(self):
        """ initialise the container 
            store in key:value format withing the certain category """

        Configuration.__instance = self

        self.__container = ConfigurationSection()
        self.loaded = False
        
    def __repr__(self):
        """ represent """

        return "<Configuration(%s)>" % (len(self.__container))

    def __add_section(self, section_name):
        """ adds a new configuration section to the main dictionary. """
        
        self.__container[section_name] = ConfigurationSection()
    
    def __remove_section(self, section_name):
        """ removes a section from the main dictionary. """
        
        del self.__container[section_name]

    def has_section(self, section_name):
        """ return if x has a section """

        return section_name in self.__container

    def get_section(self, section_name):
        """ return a raw/direct reference to a section """

        return self.__container[section_name] if self.__container.__contains__(section_name) else None
    
    def unload(self):
        """ unload an entire configuration """

        self.__container.clear()
        self.loaded = False
    
    def reload(self):
        """ reload the configuration from the initially specified file """

        self.unload()
        self.load(self._filename)
    
    def load(self, file):
        """ load a file and read in the categories and variables """

        self._filename = file
        try: f = open(file, 'r')
        except IOError, e:
            return
        if self.loaded: self.__container.clear()
        section_name = None
        for line in f.readlines():
            line = line.strip('\n')
            if line.startswith('#') or line.startswith('//'):
                continue
            elif line.endswith('{'):
                # section
                section_name = line.split('{')[0].strip()
                self.__add_section(section_name)
                continue
            elif line.startswith('}') and line.endswith('}'):
                section_name = None
                continue
            elif '=' in line:
                set = line.split('=')
                l = len(set[0])
                # strip whitespace
                set[0] = set[0].strip()
                set[1] = set[1].lstrip() if set[1] is not '' or ' ' else None
                section = self.get_section(section_name)
                section.set(set[0], set[1])
                continue
            else:
                continue
        self.loaded = True
        f.close()