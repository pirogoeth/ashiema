#!/usr/bin/env python

import os, logging, shelve, core
from core import CorePlugin, Event, get_connection, md5
from core.CorePlugin import Plugin

class IdentificationPlugin(Plugin):
    def __init__(self, connection, eventhandler):
        Plugin.__init__(self, connection, eventhandler)
        
        self.eventhandler.get_default_events()['PMEvent'].register(self.handler)
        
        self.logins = {}
        self._opened = False

        self.__open_shelve__()
        
    def __deinit__(self):
        self.eventhandler.get_default_events()['PMEvent'].deregister(self.handler)
        
        self.__close_shelve__()
    
    def __open_shelve__(self):
        if get_connection().configuration.has_category('identification'):
            shelf_loc = get_connection().configuration.get_value('identification', 'file')
        else:
            assert False, 'Identification shelf configuration not available.'
        try:
            self.shelf = shelve.open(shelf_loc, writeback = True)
        except: self.shelf = None
        self._opened = True
    
    def __close_shelve__(self):
        assert self._opened, 'Shelf is not opened.'
        
        self.shelf.sync()
        self.shelf.close()
    
    def __check_user__(self, username):
        assert self._opened, 'Shelf is not opened.'
        
        return username in self.shelf
    
    def require_level(level = 0):
        """ permission level filter """
        def wrapper(function):
            def new(*args, **kw):
                if level not in xrange(0, 4):
                    logging.getLogger('ashiema').error('invalid permission level range for %s' % (function))
                    return False
                try: data = args[1]
                except:
                    logging.getLogger('ashiema').error('could not get Serialise instance')
                    return False
                if not self.__check_user__(str(data.origin)):
                    data.origin.message('please log in to use this function.')
                    return False
                relative = self.logins[str(data.origin)]
                level_r = self.shelf[relative]['level']
                if level_r < level:
                    data.origin.message('you do not have the permissions required to use this command.')
                    return False
                elif level_r >= level:
                    return function(*args, **kw)
            return new
        return wrap
    
    def handler(self, data):
        if data.message == (0, 'login'):
            try: 
                username = data.message[1]
                password = data.message[2]
            except (IndexError):
                data.origin.message('invalid parameters.')
                return
            if not self.__check_user__(username):
                data.origin.message('invalid username.')
                return
            if self.__check_user__(username) and md5(password) == self.shelf[username]['password']:
                self.logins.update(
                    {
                        data.origin.to_s(): username
                    }
                )
                data.origin.message('logged in as %s' % (username))
                return
            elif md5(password) != self.shelf[username]['password']:
                data.origin.message('invalid password.')
                return
        elif data.message == (0, 'register'):
            try:
                username = data.message[1]
                password = data.message[2]
            except (IndexError):
                data.origin.message('invalid parameters.')
                return
            if len(password) >= 8:
                self.shelf.update(
                    {
                        username: 
                            {
                                'password' : md5(password),
                                'level'    : 0
                            }
                    }
                )
                data.origin.message('registered as %s.' % (username))
                self.shelf.sync()
                return
            else:
                data.origin.message('password must be greater than or equal to eight characters.')
                return
        elif data.message == (0, 'setlevel'):
            try:
                username = data.message[1]
                level = data.message[2]
                level = int(level)
            except (IndexError):
                data.origin.message('invalid parameters.')
                return
            if self.__check_user__(data.origin.to_s()):
                if self.shelf[data.origin.to_s()]['level'] == 3:
                    if username not in self.shelve:
                        data.origin.message('invalid username.')
                        return
                    elif level not in xrange(0, 4):
                        data.origin.message('invalid permissions level.')
                        return
                    self.shelve[username].update(
                        {
                            'level': level
                        }
                    )
                    data.origin.message('set permission level %s to %d' % (username, level))
                    self.shelf.sync()
                    return
                else:
                    data.origin.message('you do not have the permission to set levels.')
                    return
            elif not self.__check_user__(data.origin.to_s()):
                data.origin.message('you are not a registered user.')
                return

__data__ = {
    'name'     : 'IdentificationPlugin',
    'version'  : '1.0',
    'require'  : [],
    'main'     : IdentificationPlugin
}