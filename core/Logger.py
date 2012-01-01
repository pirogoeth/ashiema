#!/usr/bin/env python

import logging
from logging import handlers

def set_debug(debug):
    if debug is True:
        logging.getLogger('ashiema').setLevel(logging.DEBUG)
    else: logging.getLogger('ashiema').setLevel(logging.INFO)
    
def setup_logger():
    log = logging.getLogger("ashiema")
    handler = handlers.RotatingFileHandler("logs/ashiema.log", maxBytes = 10000, backupCount = 5)
    formatter = logging.Formatter('{%(name)s}[%(levelname)s/%(asctime)s]: %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
