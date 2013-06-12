#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import logging, cStringIO, sys
from logging import handlers

_path = "logs/ashiema.log"

def set_debug(debug):
    if debug is True:
        logging.getLogger('ashiema').setLevel(logging.DEBUG)
    else: logging.getLogger('ashiema').setLevel(logging.INFO)

def set_path(path = "logs/ashiema.log"):
    global _path
    
    _path = path

def set_level(level = "info"):
    _levels = {
        "debug"    : logging.DEBUG,
        "info"     : logging.INFO,
        "error"    : logging.ERROR,
        "warning"  : logging.WARNING,
        "critical" : logging.CRITICAL
    }
    
    logging.getLogger('ashiema').setLevel(_levels[level])

def setup_logger(stream = False):
    global _path

    log = logging.getLogger("ashiema")

    if stream is True:
        s = logging.StreamHandler()
        s.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        log.addHandler(s)

    handler = handlers.RotatingFileHandler(_path, maxBytes = 10000, backupCount = 5)
    formatter = logging.Formatter('{%(name)s}[%(levelname)s/%(asctime)s]: %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    
class StdoutLoggingHandler(object):
    
    def __init__(self):
    
        self.logger = logging.getLogger('ashiema')
    
    def write(self, data):
    
        if data.lstrip().rstrip() == '': return
        
        self.logger.debug(data.lstrip().rstrip())
    
    def close(self):
    
        pass
    
    def flush(self):
    
        pass