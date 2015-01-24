#!/usr/bin/env python2.7

import sqlite3, types, logging, malibu
from util import get_caller
from Events import Event
from EventHandler import EventHandler
from malibu.database.dbmapper import DBMapper

class DBManager(object):

    __instance = None
    
    @staticmethod
    def get_instance():

        return __instance

    def __init__(self):

        self.__maps = []
        self._log = logging.getLogger('ashiema')
        
        try: self.__db = sqlite3.connect(db_uri)
        except: self.__db = None

        self.__dbrevent = DBReadyEvent()
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

class DBReadyEvent(Event):

    def __init__(self):
        
        Event.__init__(self, "DBReadyEvent")
        self.__register__()
    
    def match(self, data):
    
        pass
    
    def run(self, data):
        
        for callback in self.callbacks.values():
            callback(data)
