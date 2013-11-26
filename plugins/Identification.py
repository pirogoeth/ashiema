#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, logging, shelve, core, traceback
from core import Plugin, Events, HelpFactory, md5, util
from core.Plugin import Plugin
from core.HelpFactory import Contexts, CONTEXT, DESC, PARAMS, ALIASES
from core.util import Escapes

class IdentificationPlugin(Plugin):

    def __init__(self):

        Plugin.__init__(self, needs_dir = True)
        
        self.eventhandler.get_events()['PMEvent'].register(self.handler)
        
        self.logins = {}
        self.accounts = {}
        self._opened = False

        self.__open_shelve__()

        self.__depersist_logins__()
        
    def __deinit__(self):

        self.eventhandler.get_events()['PMEvent'].deregister(self.handler)
        
        self.__persist_logins__()
        
        self.__close_shelve__()
    
    def __open_shelve__(self):

        try:
            self.shelf = shelve.open(self.get_path() + "users", flag = 'c', protocol = 0, writeback = True)
            self.accounts.update(self.shelf)
        except Exception as e:
            self.shelf = None
            [self.log_error(trace) for trace in traceback.format_exc(4).split('\n')]
        self._opened = True
    
    def __close_shelve__(self):

        assert self._opened, "Shelf is not opened."
        
        self.shelf.update(self.accounts)
        self.shelf.sync()
        self.shelf.close()
    
    def __persist_logins__(self):
    
        assert self._opened, "Accounts not loaded."
        
        if len(self.logins) == 0:
            print 'no logins to persist'
            pass
        
        _path = self.get_path() + "persist.db"
        
        if not os.path.isfile(_path):
            return
        
        try:
            persistance_shelf = shelve.open(self.get_path() + "persist.db", flag = 'c', protocol = 0, writeback = True)
            persistance_shelf.update(self.logins)
            persistance_shelf.sync()
            persistance_shelf.close()
        except Exception as e:
            persistance_shelf = None
            [self.log_error(trace) for trace in traceback.format_exc(4).split('\n')]

    def __depersist_logins__(self):
    
        assert self._opened, "Accounts not loaded."
        
        _path = self.get_path() + "persist.db"
        
        if not os.path.isfile(_path):
            return
        
        try:
            persistance_shelf = shelve.open(self.get_path() + "persist.db", flag = 'c', protocol = 0, writeback = True)
            self.logins.update(persistance_shelf)
            persistance_shelf.close()
        except Exception as e:
            persistance_shelf = None
            [self.log_error(trace) for trace in traceback.format_exc(4).split('\n')]
        finally:
            del persistance_shelf
            if os.path.isfile(_path):
                os.remove(_path)

    def __check_user__(self, username):

        assert self._opened, "Shelf is not opened."
        
        return username in self.accounts
    
    def __check_login__(self, origin):

        return origin in self.logins
    
    def require_level(self, data, level):

        """ permission level filter """
        if level not in xrange(0, 3):
            self.log_error('Invalid permission level range.')
            return False
        if not self.__check_login__(str(data.origin)):
            data.origin.notice('Please log in to use this function.')
            return False
        relative = self.logins[str(data.origin)]
        level_r = self.accounts[relative]['level']
        if level_r < level:
            data.origin.notice('You do not have the permissions required to use this command.')
            return False
        elif level_r >= level:
            return True
    
    def handler(self, data):

        if data.message == (0, 'login'):
            try: 
                if len(data.message[1:]) == 2:
                    username = data.message[1]
                    password = data.message[2]
                elif len(data.message[1:]) == 1:
                    username = data.origin.nick
                    password = data.message[1]
                else:
                    raise IndexError('Invalid number of arguments specified')
            except (IndexError):
                data.origin.notice('Invalid parameters.')
                return
            if not self.__check_user__(username):
                data.origin.notice('Invalid username.')
                return
            if self.__check_login__(data.origin.to_s()):
                data.origin.notice('You are already logged in.')
                return
            elif self.__check_user__(username) and md5(password) == self.accounts[username]['password']:
                self.logins.update(
                    {
                        data.origin.to_s(): username
                    }
                )
                data.origin.notice('Logged in as %s%s%s.' % (Escapes.BOLD, username, Escapes.BOLD))
                return
            elif md5(password) != self.accounts[username]['password']:
                data.origin.notice('Invalid password.')
                return
        elif data.message == (0, 'logout'):
            if not self.__check_login__(data.origin.to_s()):
                data.origin.notice('You are not logged in.')
                return
            del self.logins[data.origin.to_s()]
            data.origin.notice('You have been logged out.')
            return
        elif data.message == (0, 'register'):
            try:
                username = data.message[1]
                password = data.message[2]
            except (IndexError):
                data.origin.notice('Invalid parameters.')
                return
            if len(password) >= 8:
                self.accounts.update(
                    {
                        username: {
                                'password' : md5(password),
                                'level'    : 0
                        }
                    }
                )
                data.origin.notice('Registered as %s.' % (username))
                self.accounts.sync()
                return
            else:
                data.origin.notice('Password %smust%s be greater than or equal to eight characters.' % (Escapes.BOLD, Escapes.BOLD))
                return
        elif data.message == (0, 'setlevel'):
            try:
                username = data.message[1]
                level = data.message[2]
                level = int(level)
            except (IndexError):
                data.origin.notice('Invalid parameters.')
                return
            if self.__check_user__(data.origin.to_s()):
                if self.accounts[data.origin.to_s()]['level'] == 2:
                    if username not in self.shelve:
                        data.origin.notice('Invalid username.')
                        return
                    elif level not in xrange(0, 3):
                        data.origin.notice('Invalid permissions level.')
                        return
                    self.shelve[username].update(
                        {
                            'level': level
                        }
                    )
                    data.origin.notice('Set permission level for %s%s%s to %s%d%s.' % (Escapes.BOLD, username, Escapes.BOLD, Escapes.BOLD, levelEscapes.BOLD))
                    self.accounts.sync()
                    return
                else:
                    data.origin.notice('You do not have access to permission levels.')
                    return
            elif not self.__check_user__(data.origin.to_s()):
                data.origin.notice('You are not a registered user.')
                return

__data__ = {
    'name'     : 'IdentificationPlugin',
    'version'  : '1.0',
    'require'  : ['SystemPlugin'],
    'main'     : IdentificationPlugin,
    'events'   : []
}

__help__ = {
    'login'    : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Identifies you with the bot and gives you permission to perform actions.',
        PARAMS  : '<username> <password>',
        ALIASES : []
    },
    'logout'   : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Removes your session from the bot, removing access permissions.',
        PARAMS  : '',
        ALIASES : []
    },
    'register' : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Creates an account for the bot to identify you with.',
        PARAMS  : '<username> <password>',
        ALIASES : []
    },
    'setlevel' : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Sets the access level of the specified account.',
        PARAMS  : '<username> <accesslevel>',
        ALIASES : []
    }
}