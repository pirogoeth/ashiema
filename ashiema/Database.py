#!/usr/bin/env python2.7

import sqlite3, logging, types, inspect, traceback
from Events import Event
from EventHandler import EventHandler

class DBManager(object):

    __instance = None
    
    @staticmethod
    def get_instance():

        return __instance

    def __init__(self, db_uri):

        try: self.__db = sqlite3.connect(db_uri)
        except: self.__db = None

        self.__maps = []
        
        self.__dbrevent = DBReadyEvent()
        EventHandler.get_instance().get_event("PluginsLoadedEvent").register(self.__on_plugins_loaded)
    
    def __on_plugins_loaded(self):
    
        EventHandler.get_instance().fire_once(self.__dbrevent, (None))

    def register_mapper(self, map):

        if not isinstance(map, DBMapper):
            pass

class DBMapper(object):

    def __init__(self, db, keys, keytypes, options = {'primaryIndex' : 0, 'autoincrIndex' : True}):

        self._db = db
        self._options = options
        self._table = self.__class__.__name__.lower() if 'tableName' not in self._options else self._options['tableName']

        self._keys = keys
        self._keytypes = keytypes

        self._primary_ind = self._options['primaryIndex']
        self._autoincr_ind = self._options['autoincrIndex']

        self._primary = self._keys[self._primary_ind]

        self.__generate_structure()
        self.__generate_getters()
        self.__generate_setters()
        self.__generate_properties()

    def __log_execute(self, cur, sql, fetch = 'one', limit = -1, args = ()):
        
        query = sql
        try:
            if len(args) >= 1:
                cur.execute("select " + ", ".join(["quote(?)" for i in args]), args)
                quoted_values = cur.fetchone()
                for quoted_value in quoted_values:
                    query = query.replace('?', str(quoted_value), 1)
        except: pass 
        try: cur.execute(query)
        except (sqlite3.ProgrammingError): cur.execute(query, args)
        if fetch == 'one':
            return cur.fetchone()
        elif fetch == 'many':
            if limit == -1: limit = cur.arraysize
            return cur.fetchmany(size = limit)
        elif fetch == 'all':
            return cur.fetchall()
        else:
            return cur.fetchall()

    def __get_table_info(self):

        cur = self._db.cursor()
        query = "pragma table_info(%s)" % (self._table)
        return self.__log_execute(cur, query, fetch = 'all')

    def __generate_structure(self):

        # use pragma constructs to get table into
        tblinfo = self.__get_table_info()

        # create the table if the statement does not exist
        if len(tblinfo) == 0:
            ins = zip(self._keys, self._keytypes)
            typarr = []
            for pair in ins:
                if pair[0] == self._primary:
                    # identifier type primary key
                    if self._autoincr_ind:
                        typarr.append("%s %s primary key autoincrement" % (pair[0], pair[1]))
                    else:
                        typarr.append("%s %s primary key" % (pair[0], pair[1]))
                else:
                    # identifier type
                    typarr.append("%s %s" % (pair[0], pair[1]))
            cur = self._db.cursor()
            # create table if not exists <table> (<typarr>)
            query = "create table if not exists %s (%s)" % \
                (self._table, ', '.join(typarr))
            self.__log_execute(cur, query)

        # make sure table columns are up to date.
        if len(tblinfo) > 0:
            # use pragma table info to build database schema
            schema_ids = []
            schema_types = []
            for col in tblinfo:
                schema_ids.append(col[1])
                schema_types.append(col[2])
            # use schema to determine / apply database updates
            schema_updates = []
            for pair in zip(self._keys, self._keytypes):
                if pair[0] in schema_ids:
                    continue
                else:
                    schema_updates.append("%s %s" % (pair[0], pair[1]))
            for defn in schema_updates:
                query = "alter table %s add column %s" % (self._table, defn)
                cur = self._db.cursor()
                self.__log_execute(cur, query)

    def __generate_getters(self):

        for _key in self._keys:
            def getter_templ(self, __key = _key):
                if __key not in self._keys:
                    return
                cur = self._db.cursor()
                # select * from table where key=<key>
                query = "select %s from %s where %s=?" % (__key, self._table, self._primary)
                result = self.__log_execute(cur, query, args = (getattr(self, "_%s" % (self._primary)),))
                try: return result[0]
                except: return result
            setattr(self, "get_%s" % (_key), types.MethodType(getter_templ, self))

    def __generate_setters(self):

        for _key in self._keys:
            def setter_templ(self, value, __key = _key):
                if __key not in self._keys:
                    return
                cur = self._db.cursor()
                # update table set key=value where primary=id
                query = "update %s set %s=? where %s=?" % (
                    self._table, __key, self._primary)
                self.__log_execute(cur, query, args = (value, getattr(self, "_%s" % (self._primary)),))
                setattr(self, "_%s" % (__key), value)
            setattr(self, "set_%s" % (_key), types.MethodType(setter_templ, self))

    def __generate_properties(self):

        for _key in self._keys:
            setattr(self, "_%s" % (_key), None)
        
        for _key in self._keys:
            getf = getattr(self, "get_%s" % (_key))
            setf = getattr(self, "set_%s" % (_key))
            setattr(self, _key, property(getf, setf, None, "[%s] property"))

    def create(self):

        cur = self._db.cursor()
        vals = []
        for key in self._keys:
            if key == self._primary and self._autoincr_ind:
                vals.append(None) # Put None in for the index since it's going to be autoincr'd
            else:
                vals.append(getattr(self, "_%s" % (key)))
        qst = ', '.join(["?" for item in vals])
        query = "insert into %s values (%s)" % (self._table, qst)
        self.__log_execute(cur, query, args = vals)
        setattr(self, "_%s" % (self._primary), cur.lastrowid)

    def load(self, **kw):

        cur = self._db.cursor()
        keys = []
        vals = []
        for key, val in kw.iteritems():
            keys.append(key)
            vals.append(val)
        whc = []
        for pair in zip(keys, vals):
            whc.append("%s=?" % (pair[0]))
        query = "select * from %s where %s" % (self._table, ','.join(whc))
        result = self.__log_execute(cur, query, args = vals)
        for key, dbv in zip(self._keys, result):
            setattr(self, "_%s" % (key), dbv)

    def save(self):

        self._db.commit()

class DBReadyEvent(Event):

    def __init__(self):
        
        Event.__init__(self, "DBReadyEvent")
        self.__register__()
    
    def match(self, data):
    
        pass
    
    def run(self, data):
        
        for callback in self.callbacks.values():
            callback(data)
