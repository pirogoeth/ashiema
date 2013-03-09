#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>. """

import core, sys
from core import Connection, Logger, util
from core.util import Configuration, fork

def main(conf_file):
    _config = Configuration.Configuration()
    _config.load(conf_file)
    connection = Connection.Connection(_config)
    Logger.setup_logger(stream = (_config.get_value('main', 'fork') != 'True' or _config.get_value('main', 'fork') != 'true'))
    core._connection = connection
    log_level = _config.get_value('logging', 'level')
    if _config.get_value('main', 'debug') == 'True' or _config.get_value('main', 'debug') == 'true':
        connection.set_debug(True)
    else: connection.set_debug(False)
    Logger.set_level(log_level)
    connection.setup_info(
        nick     = _config.get_value('main', 'nick'),
        ident    = _config.get_value('main', 'ident'),
        real     = _config.get_value('main', 'real')
    )
    if _config.get_value('main', 'fork') == 'True' or _config.get_value('main', 'fork') == 'true':
        fork()
    connection.connect(
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
