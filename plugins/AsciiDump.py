# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013-2015 Sean Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, logging, ashiema, traceback
import ashiema, malibu, os, traceback

from ashiema.api.events import Event
from ashiema.api.help import Contexts, CONTEXT, DESC, PARAMS, ALIASES
from ashiema.api.plugin import Plugin
from ashiema.util import Escapes

from malibu.util.log import LoggingDriver

from contextlib import closing


class AsciiDump(Plugin):

    def __init__(self, needs_dir = True, needs_comm_pipe = False):

        Plugin.__init__(self, needs_dir, needs_comm_pipe)
        
        self.get_event("MessageEvent").register(self.handler)
        self.get_event("PluginsLoadedEvent").register(self.__on_plugins_loaded)
    
    def __deinit__(self):
    
        self.get_event("MessageEvent").deregister(self.handler)
        self.get_event("PluginsLoadedEvent").deregister(self.__on_plugins_loaded)

    def __on_plugins_loaded(self):
    
        self.identification = self.get_plugin("IdentificationPlugin")
    
    def __is_contained(self, master, target):
    
        if os.path.abspath(master) in os.path.abspath(target):
            return True
        else:
            return False
    
    def handler(self, data):
    
        if data.message == (0, "@ascii-dump"):
            assert self.identification.require_level(data, 1)
            try:
                artfile = data.message[1]
            except IndexError:
                data.target.message("%s[AsciiDump]: %sPlease provide the name of an art file to dump." % (Escapes.BOLD, Escapes.GREEN))
                return
            try:
                file_path = self.get_path() + "%s.txt" % (artfile)
                if not self.__is_contained(self.get_path(), file_path):
                    data.target.message("%s[AsciiDump]: %sInvalid art file path!" % (Escapes.BOLD, Escapes.GREEN))
                    return
                with closing(open(file_path, 'r')) as art:
                    for line in art.readlines():
                        data.target.message(line)
            except IOError:
                data.target.message("%s[AsciiDump]: %sCould not open the art file." % (Escapes.BOLD, Escapes.GREEN))
            except:
                data.target.message("%s[AsciiDump]: %sAn error occurred while dumping the art file." % (Escapes.BOLD, Escapes.GREEN))
                [self.log_error(line) for line in traceback.format_exc(4).split('\n')]

__data__ = {
    'name'      : 'AsciiDump',
    'version'   : '0.1',
    'require'   : [],
    'main'      : AsciiDump,
    'events'    : []
}

__help__ = {
    '@ascii-dump' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : "Dumps an ascii text file (typically, art) into the current channel.",
        PARAMS  : "<filename>",
        ALIASES : []
    }
}
