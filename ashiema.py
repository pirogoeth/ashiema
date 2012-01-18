#!/usr/bin/env python

import core, sys
from core import Connection, Logger, util
from core.util import Configuration, fork

def main(conf_file):
    _config = Configuration.Configuration()
    _config.load(conf_file)
    connection = Connection.Connection(_config)
    Logger.setup_logger()
    core._connection = connection
    log_level = _config.get_value('logging', 'level')
    if _config.get_value('main', 'debug') == 'True' or _config.get_value('main', 'debug') == 'true':
        connection.set_debug(True)
    else: connection.set_debug(False)
    Logger.set_level(log_level)
    # fork off
    fork()
    connection.setup_info(
        nick     = _config.get_value('main', 'nick'),
        ident    = _config.get_value('main', 'ident'),
        real     = _config.get_value('main', 'real')
    ).connect(
        address  = _config.get_value('main', 'address'),
        port     = _config.get_value('main', 'port'),
        _ssl     = _config.get_value('main', 'ssl'),
        password = _config.get_value('main', 'password')
    ).run()

if __name__ == '__main__':
    try: filename = sys.argv[1]
    except IndexError:
        filename = 'bot.conf'
    main(filename)
