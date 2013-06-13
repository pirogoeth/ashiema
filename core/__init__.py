#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import hashlib

__all__ = ['Connection', 'Events', 'EventHandler', 'HelpFactory', 
       'Logger', 'Plugin', 'PluginLoader', 'Tokenizer']

version = "1.1"

def md5(data):
    _m = hashlib.md5()
    _m.update(data)
    return _m.hexdigest()