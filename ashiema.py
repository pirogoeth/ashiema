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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from core.Logger import StdoutLoggingHandler

# Try to set up redirected outputs before anything else.
#sys.stdout = StdoutLoggingHandler()
#sys.stderr = StdoutLoggingHandler()

# Import everything else and do normal setup.
import core, logging
from core import Connection, Logger, util
from core.util import Configuration, fork

def main(conf_file):
    config = Configuration.Configuration()
    config.load(conf_file)
    
    connection = Connection.Connection(config)
    core._connection = connection

    Logger.setup_logger(stream = (config.get_value('main', 'fork') != 'True' or config.get_value('main', 'fork') != 'true'))
    
    log_level = config.get_value('logging', 'level')
    
    if config.get_value('main', 'debug') == 'True' or config.get_value('main', 'debug') == 'true':
        connection.set_debug(True)
        Logger.set_level('debug')
    else: 
        connection.set_debug(False)
        Logger.set_level(log_level)

    connection.setup_info(
        nick     = config.get_value('main', 'nick'),
        ident    = config.get_value('main', 'ident'),
        real     = config.get_value('main', 'real')
    )

    if config.get_value('main', 'fork') == 'True' or config.get_value('main', 'fork') == 'true':
        fork()

    connection.connect(
        address  = config.get_value('main', 'address'),
        port     = config.get_value('main', 'port'),
        _ssl     = config.get_value('main', 'ssl'),
        password = config.get_value('main', 'password')
    ).run()

if __name__ == '__main__':

    try: filename = sys.argv[1]
    except IndexError:
        filename = 'bot.conf'
    try: main(filename)
    except AttributeError as e:
        print >> sys.__stderr__, "Invalid configuration: %s!" % (filename)
