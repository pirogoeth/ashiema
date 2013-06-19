#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without 
# restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the 
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys, core, logging, traceback
from core import Events, Logger, util
from core.Connection import Connection
from core.EventHandler import EventHandler
from core.PluginLoader import PluginLoader
from core.util import Configuration, fork
from core.util.Configuration import Configuration, ConfigurationSection

def main(conf_file):
    configuration = Configuration()
    configuration.load(conf_file)
    
    connection = Connection()
    
    config = configuration.get_section('main')
    
    Logger.setup_logger(stream = not config.get_bool('fork'))
    
    log_level = Configuration.get_instance().get_section('logging').get_string('level', 'debug')
    
    if config.get_bool('debug'):
        connection.set_debug(True)
        Logger.set_level('debug')
    else: 
        connection.set_debug(False)
        Logger.set_level(log_level)

    connection.setup_info(
        nick     = config.get_string('nick', 'ashiema'),
        ident    = config.get_string('ident', 'ashiema'),
        real     = config.get_string('real', 'ashiema IRC bot -- http://github.com/pirogoeth/ashiema')
    )

    if config.get_bool('fork'):
        fork()

    try:
        connection.connect(
            address  = config.get_string('address', '127.0.0.1'),
            port     = config.get_int('port', 6667),
            _ssl     = config.get_bool('ssl', False),
            password = config.get_string('password', None)
        )
        EventHandler.get_instance()
        Events.get_events()
        PluginLoader.get_instance()
        connection.run()
    except (SystemExit, KeyboardInterrupt):
        PluginLoader.get_instance().unload()

if __name__ == '__main__':

    try: filename = sys.argv[1]
    except IndexError:
        filename = 'bot.conf'
    try: main(filename)
    except AttributeError as e:
        print >> sys.__stderr__, "Invalid configuration: %s!" % (filename)
        traceback.print_exc(4)