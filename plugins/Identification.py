#!/usr/bin/env python

import os, logging, shelve, core, traceback
from core import CorePlugin, Event, get_connection, md5, util
from core.CorePlugin import Plugin
from core.util import Escapes

class IdentificationPlugin(Plugin):

    def __init__(self, connection, eventhandler):

        Plugin.__init__(self, connection, eventhandler, needs_dir = True)
        
        self.eventhandler.get_default_events()['PMEvent'].register(self.handler)
        
        self.logins = {}
        self._opened = False

        self.__open_shelve__()
        
    def __deinit__(self):

        self.eventhandler.get_default_events()['PMEvent'].deregister(self.handler)
        
        self.__close_shelve__()
    
    def __open_shelve__(self):

        try:
            self.shelf = shelve.open(self.get_path() + "users", protocol = 2, writeback = True)
        except Exception as e:
            self.shelf = None
            [logging.getLogger('ashiema').error(trace) for trace in traceback.format_exc(4).split('\n')]
        self._opened = True
    
    def __close_shelve__(self):

        assert self._opened, 'Shelf is not opened.'
        
        self.shelf.sync()
        self.shelf.close()
    
    def __check_user__(self, username):

        assert self._opened, 'Shelf is not opened.'
        
        return username in self.shelf
    
    def __check_login__(self, origin):

        return origin in self.logins
    
    def require_level(self, data, level):

        """ permission level filter """
        if level not in xrange(0, 4):
            logging.getLogger('ashiema').error('Invalid permission level range.')
            return False
        if not self.__check_login__(str(data.origin)):
            data.origin.message('Please log in to use this function.')
            return False
        relative = self.logins[str(data.origin)]
        level_r = self.shelf[relative]['level']
        if level_r < level:
            data.origin.message('You do not have the permissions required to use this command.')
            return False
        elif level_r >= level:
            return True
    
    def handler(self, data):

        if data.message == (0, 'login'):
            try: 
                username = data.message[1]
                password = data.message[2]
            except (IndexError):
                data.origin.message('Invalid parameters.', 'login <username> <password>')
                return
            if not self.__check_user__(username):
                data.origin.message('Invalid username.')
                return
            if self.__check_user__(username) and md5(password) == self.shelf[username]['password']:
                self.logins.update(
                    {
                        data.origin.to_s(): username
                    }
                )
                data.origin.message('Logged in as %s.' % (username))
                return
            elif md5(password) != self.shelf[username]['password']:
                data.origin.message('Invalid password.')
                return
        elif data.message == (0, 'logout'):
            if not self.__check_login__(data.origin.to_s()):
                data.origin.message('You are not logged in.')
                return
            del self.logins[data.origin.to_s()]
            data.origin.message('You have been logged out.')
            return
        elif data.message == (0, 'register'):
            try:
                username = data.message[1]
                password = data.message[2]
            except (IndexError):
                data.origin.message('Invalid parameters.', '%sregister%s    <username> <password>' % (Escapes.BOLD, Escapes.BOLD))
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
                data.origin.message('Registered as %s.' % (username))
                self.shelf.sync()
                return
            else:
                data.origin.message('Password %smust%s be greater than or equal to eight characters.' % (Escapes.BOLD, Escapes.BOLD))
                return
        elif data.message == (0, 'setlevel'):
            try:
                username = data.message[1]
                level = data.message[2]
                level = int(level)
            except (IndexError):
                data.origin.message('Invalid parameters.', '%ssetlevel%s   <username> <level>' % (Escapes.BOLD, Escapes.BOLD))
                return
            if self.__check_user__(data.origin.to_s()):
                if self.shelf[data.origin.to_s()]['level'] == 3:
                    if username not in self.shelve:
                        data.origin.message('Invalid username.')
                        return
                    elif level not in xrange(0, 4):
                        data.origin.message('Invalid permissions level.')
                        return
                    self.shelve[username].update(
                        {
                            'level': level
                        }
                    )
                    data.origin.message('Set permission level for %s%s%s to %s%d%s.' % (Escapes.BOLD, username, Escapes.BOLD, Escapes.BOLD, levelEscapes.BOLD))
                    self.shelf.sync()
                    return
                else:
                    data.origin.message('You do not have access to permission levels.')
                    return
            elif not self.__check_user__(data.origin.to_s()):
                data.origin.message('You are not a registered user.')
                return

__data__ = {
    'name'     : 'IdentificationPlugin',
    'version'  : '1.0',
    'require'  : [],
    'main'     : IdentificationPlugin
}

__help__ = {
    'login'    : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Identifies you with the bot and gives you permission to perform actions.',
        PARAMS  : '<username> <password>'
    },
    'logout'   : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Removes your session from the bot, removing access permissions.',
        PARAMS  : ''
    },
    'register' : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Creates an account for the bot to identify you with.',
        PARAMS  : '<username> <password>'
    },
    'setlevel' : {
        CONTEXT : Contexts.PRIVATE,
        DESC    : 'Sets the access level of the specified account.',
        PARAMS  : '<username> <accesslevel>'
    }
}