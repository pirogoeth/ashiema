#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, logging, ashiema, traceback, datetime, malibu
from ashiema import md5, Plugin, Events, HelpFactory, Database
from ashiema.Database import DBManager
from ashiema.Events import Event
from ashiema.Plugin import Plugin
from ashiema.HelpFactory import Contexts, CONTEXT, DESC, PARAMS, ALIASES
from ashiema.util import Escapes
from malibu.database.dbmapper import DBMapper

class Authentication(Plugin):

    def __init__(self):
    
        Plugin.__init__(self, needs_dir = True, needs_comm_pipe = False)
        
        self.get_event("DBReadyEvent").register(self.__on_db_ready)
    
    def __on_db_ready(self):
    
        DBManager.get_instance().register_mapper(User)
        DBManager.get_instance().register_mapper(Session)
        DBManager.get_instance().register_mapper(AuthActivity)
    
    def __load(self):
    
        pass
    
    def get_user_dbm(self):

        return User

    def get_session_dbm(self):

        return Session

    def get_auth_activity_dbm(self):

        return AuthActivity
    
    def user_login(self, context, username, password):
    
        aa = AuthActivity.get_new_authactivity()
        aa.set_actor(context.user.to_s())

        s = Session()
        s.find(user_ident = context.user.to_s())
        if s.get_user_id() and s.get_active():
            aa.set_event_type("USER_LOGIN_FAIL_EXISTS")
            raise SessionException("Session is already active.")
        elif s.get_user_id() is None:
            s.create()
        u = User()
        u.find(username = username)
        if not u.get_user_id():
            aa.set_event_type("USER_LOGIN_FAIL_NOT_EXISTS")
            raise UserException("Invalid username or password.") 
        authtok = md5(password)
        if authtok == u.get_authtoken():
            s.set_active(True)
            s.set_user_id(u.get_user_id())
            s.set_start_time(datetime.datetime.now())
        else:
            aa.set_event_type("USER_LOGIN_FAIL_INVALID_AUTHTOKEN")
            raise UserException("Invalid username or password.")
    
    def user_logout(self, context):
    
        aa = AuthActivity.get_new_authactivity()
        aa.set_actor(context.user.to_s())

        s = Session()
        s.find(user_ident = context.user.to_s())
        if not s.get_user_id():
            aa.set_event_type("USER_LOGOUT_FAIL")
            raise SessionException("No session exists for %s." % (context.user.to_s()))
        if s.get_active():
            aa.set_event_type("USER_LOGOUT")
            aa.set_user_id(s.get_user_id())
            aa.set_session_id(s.get_session_id())
            s.set_active(False)
            return s
        else:
            aa.set_event_type("USER_LOGOUT_FAIL")
            raise SessionException("Session is already closed.")
    
    def user_register(self, context, username, password):
    
        aa = AuthActivity.get_new_authactivity()
        aa.set_actor(context.user.to_s())

        u = User()
        u.find(username = username)
        if u.get_user_id() is not None:
            aa.set_event_type("USER_REGISTER_FAIL_EXISTS")
            raise UserException("User %s already exists." % (username))
        pwtok = md5(password)
        u.create()
        u.set_username(username)
        u.set_authtoken(pwtok)
        aa.set_event_type("USER_REGISTER")
        aa.set_user_id(u.get_user_id())

        return u
    
    def user_setlevel(self, context, username, privilege):
    
        pass # XXX - implement

class UserException(Exception):

    def __init__(self, value):

        self.value = value

    def __str__(self):

        return repr(self.value)

class SessionException(Exception):

    def __init__(self, value):

        self.value = value

    def __str__(self):

        return repr(self.value)

class User(DBMapper):

    def __init__(self):
    
        db = DBManager.get_instance().get_database()
        keys =      ['user_id', 'username', 'authtoken',    'last_login', 'last_addr',  'totp_enabled', 'totp_secret',  'permission', 'fail_count']
        ktypes =    ['integer', 'text',     'text',         'datetime'    'text',       'boolean',      'text'          'integer',    'integer']
       
        User.set_db_options(db, keys, ktypes)

        DBMapper.__init__(self, db, keys, ktypes)

class Session(DBMapper):

    def __init__(self):

        db = DBManager.get_instance().get_database()
        keys =      ['session_id',  'start_time',   'active',   'seclevel',     'user_id',  'user_ident']
        ktypes =    ['integer',     'datetime',     'boolean',  'integer',      'integer',  'text']

        Session.set_db_options(db, keys, ktypes)

        DBMapper.__init__(self, db, keys, ktypes)

class AuthActivity(DBMapper):

    @staticmethod
    def get_new_authactivity():

        aa = AuthActivity()
        aa.create()
        aa.set_event_time(datetime.datetime.now())

    def __init__(self):

        db = DBManager.get_instance().get_database()
        keys =      ['act_id',      'event_time',   'user_id',      'session_id',       'event_type',       'actor']
        ktypes =    ['integer',     'datetime',     'integer',      'integer',          'text',             'text']

        AuthActivity.set_db_options(db, key, ktypes)

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
