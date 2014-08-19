#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import logging, cStringIO, sys, os
from logging import handlers

def set_debug(debug):
    if debug is True:
        logging.getLogger('ashiema').setLevel(logging.DEBUG)
    else: logging.getLogger('ashiema').setLevel(logging.INFO)

def set_level(level = "info"):
    _levels = {
        "debug"    : logging.DEBUG,
        "info"     : logging.INFO,
        "error"    : logging.ERROR,
        "warning"  : logging.WARNING,
        "critical" : logging.CRITICAL
    }
    
    logging.getLogger('ashiema').setLevel(_levels[level])

def setup_logger(stream = False, path = "logs/ashiema.log"):
    basedir = os.path.dirname(path)
    if not os.path.exists(basedir):
        os.mkdir(basedir)

    logger = logging.getLogger("ashiema")

    if stream is True:
        s = logging.StreamHandler()
        s.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(s)

    handler = handlers.RotatingFileHandler(path, maxBytes = 64000000, backupCount = 5)
    formatter = logging.Formatter('{%(name)s}[%(levelname)s/%(asctime)s]: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
