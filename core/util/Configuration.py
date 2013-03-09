#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

class Configuration(object):
    """ this will hold the configuration.
        it will not actually read the configuration itself, but it
        will carry everything """
    
    def __init__(self):
        """ initialise the container 
            store in key:value format withing the certain category """
        self.container = {}
        self.loaded = False
        
    def __repr__(self):
        """ represent """
        return "<Configuration(%s)>" % (len(self.container))

    def __add__(self, set):
        """ addition function to add a set to the container """
        self.container[set[2]].update({set[0]: set[1]})
    
    def __sub__(self, set):
        """ subtraction function to remove a set from a category. """
        self.container[set[0]].__delitem__(set[1])
    
    def __iadd__(self, category):
        """ p/e function to add a category """
        self.container.update({category: {}})
        return self
    
    def __isub__(self, category):
        """ s/e function to remove a category """
        if self.container[category]:
            self.container.__delitem__(category)
        return self
    
    def has_category(self, category):
        """ return if x has a category """
        return category in self.container

    def get_category(self, category):
        """ return a category """
        return self.container[category] if self.container.__contains__(category) else None
    
    def get_value(self, category, key):
        """ return [category:key] """
        value = self.container[category][key] if self.container[category].__contains__(key) else None
        if value is None: return value
        else:
            if value.startswith(':'):
                """ this is a reference to another variable. """
                return self.get_value(category, value[1:])
            else: return value
    
    def unload(self):
        """ unload an entire configuration """
        self.container.clear()
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
        if self.loaded: self.container.clear()
        category = None
        for line in f.readlines():
            line = line.strip('\n')
            if line.startswith('#') or line.startswith('//'):
                continue
            elif line.endswith('{'):
                # category
                category = line.split('{')[0].strip()
                self += category
                continue
            elif line.startswith('}') and line.endswith('}'):
                category = None
            elif '=' in line:
                set = line.split('=')
                l = len(set[0])
                # strip whitespace
                set[0] = set[0].strip()
                set[1] = set[1].lstrip() if set[1] is not '' or ' ' else None
                set.append(category)
                self + set
                continue
            continue
        self.loaded = True
        f.close()