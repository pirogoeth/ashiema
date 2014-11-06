#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, logging, ashiema, traceback
from ashiema import md5, Plugin, Events, HelpFactory, Database
from ashiema.Database import DBManager, DBMapper
from ashiema.Events import Event
from ashiema.Plugin import Plugin
from ashiema.HelpFactory import Contexts, CONTEXT, DESC, PARAMS, ALIASES
from ashiema.util import Escapes

class Authentication(object):

    def __init__(self):
    
        Plugin.__init__(self, needs_dir = True, needs_comm_pipe = False)
        
        self.get_event("DBReadyEvent").register(self.__on_db_ready)
    
    def __on_db_ready(self):
    
        DBManager.get_instance().register_mapper(User)
        DBManager.get_instance().register_mapper(Session)
    
    def __load(self):
    
        pass
    
    def get_user_dbm(self):

        return User

    def get_session_dbm(self):

        return Session
    
    def user_login(self, username, password):
    
        pass
    
    def user_logout(self, username):
    
        pass
    
    def user_register(self, username, password):
    
        u = User()
        u.find(username = username)
    
    def user_setlevel(self, username, privilege):
    
        pass

class User(DBMapper):

    def __init__(self):
    
        db = DBManager.get_instance().get_database()
        keys =      ['user_id', 'username', 'authtoken',    'last_login', 'last_addr',  'totp_enabled', 'totp_secret',  'permission', 'fail_count']
        ktypes =    ['integer', 'text',     'text',         'datetime'    'text',       'boolean',      'text'          'integer',    'integer']
        
        DBMapper.__init__(self, db, keys, ktypes)

class Session(DBMapper):

    def __init__(self):

        db = DBManager.get_instance().get_database()
        keys =      ['session_id',  'start_time',   'seclevel',     'user_id']
        ktypes =    ['integer',     'datetime',     'integer',      'integer']

        DBMapper.__init__(self, db, keys, ktypes)

class UserLogonEvent(Event):

    pass

class UserLogoffEvent(Event):

    pass

class UserRegisterEvent(Event):

    pass

__data__ = {
    'name'      : 'Authentication',
    'version'   : '0.1',
    'require'   : [],
    'main'      : Authentication,
    'events'    : [UserLogonEvent, UserLogoffEvent, UserRegisterEvent]
}

__help__ = {
    'login'     : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Authenticates you with the bot and grants permission to perform certain actions.',
        PARAMS  : '[username] <password>',
        ALIASES : []
    },
    'logout'    : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Removes your session and clears your permissions.',
        PARAMS  : '',
        ALIASES : []
    },
    'register'  : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Registers an account with the backend authentication provider, if available.',
        PARAMS  : '<username> [password]',
        ALIASES : []
    },
    'setlevel'  : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Sets the privilege level of the specified account.',
        PARAMS  : '<username> <access level>',
        ALIASES : []
    }
}
