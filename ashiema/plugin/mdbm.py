# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013-2015 Sean Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import ashiema, sqlite3, types, malibu

from ashiema.api.events import Event
from ashiema.irc.eventhandler import EventHandler
from ashiema.util import get_caller

from malibu.database.dbmapper import DBMapper
from malibu.util.log import LoggingDriver


class MDBManager(object):

    __instance = None

    @staticmethod
    def get_instance():

        return __instance

    def __init__(self):

        self.__maps = []
        self._log = LoggingDriver.find_logger()

        try: self.__db = sqlite3.connect(db_uri)
        except: self.__db = None

        self.__dbrevent = MDBReadyEvent()
        EventHandler.get_instance().get_event("PluginsLoadedEvent").register(self.__on_plugins_loaded)

        # self.__tbl_conflict_check()

    def __on_plugins_loaded(self):

        EventHandler.get_instance().fire_once(self.__dbrevent, (None))

    def __tbl_conflict_check(self):

        tbl_names = [dbm._table for dbm in self.__maps]

        for dbm, name in zip(self.__maps, tbl_names):
            pass

    def get_database(self):

        return self.__db

    def register_mapper(self, mapper):

        if not isinstance(mapper, DBMapper):
            pass

        self.__maps.append(mapper)

        self._log.debug("Registered database mapper from [%s]" % (get_caller()))

class MDBReadyEvent(Event):

    def __init__(self):

        Event.__init__(self, "MDBReadyEvent")
        self.__register__()

    def match(self, data):

        pass

    def run(self, data):

        for callback in self.callbacks.values():
            callback(data)
