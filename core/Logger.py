#!/usr/bin/env python

import logging
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

def setup_logger():
    global _path

    log = logging.getLogger("ashiema")
    handler = handlers.RotatingFileHandler(_path, maxBytes = 10000, backupCount = 5)
    formatter = logging.Formatter('{%(name)s}[%(levelname)s/%(asctime)s]: %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
