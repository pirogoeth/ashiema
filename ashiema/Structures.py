#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import re, logging

import Connection

class Structure(object):

    @staticmethod
    def log_debug(*args):
    
        [logging.getLogger('ashiema').debug(line) for line in args]        

    @staticmethod
    def log_info(*args):
    
        [logging.getLogger('ashiema').info(line) for line in args]        

    @staticmethod
    def log_warning(*args):
    
        [logging.getLogger('ashiema').warning(line) for line in args]        

    @staticmethod
    def log_error(*args):
    
        [logging.getLogger('ashiema').error(line) for line in args]        

    @staticmethod
    def log_critical(*args):
    
        [logging.getLogger('ashiema').critical(line) for line in args]

class Origin(Structure):

    def __init__(self, name):
    
        self.connection = Connection.Connection.get_instance()
        self.name = name

    def __repr__(self):
    
        return str(self.name)

    def to_s(self):

        return str(self.name)

class Channel(Structure):

    __channels = {}
    
    @staticmethod
    def format_topic(channel, topic):
    
        return "TOPIC %s :%s" % (channel, topic)

    @staticmethod
    def format_privmsg(channel, message):
    
        return "PRIVMSG %s :%s" % (channel, message)

    @staticmethod
    def format_notice(channel, message):
    
        return "NOTICE %s :%s" % (channel, message)

    @staticmethod
    def format_join(channel, key = None):
    
        if key is not None:
            return "JOIN %s" % (channel)
        return "JOIN %s :%s" % (channel, key)

    @staticmethod
    def format_kick(channel, username, reason = "Your behaviour is not conductive to the desired environment."):
    
        return "KICK %s %s :%s" % (channel, username, reason)

    @staticmethod
    def format_who(channel):
        """ requests list of channel members with information in format: <channel> <host> <nick> <account> """
    
        return "WHO %s %achn" % (channel)

    @staticmethod
    def join(channel, key = None):
        """ assembles a join message. """
        
        if key is None:
            message = Channel.format_join(channel)
        else: message = Channel.format_join(channel, key)
        
        return message

    @staticmethod
    def get_channel(channel):
        """ returns a channel with a given name. """
        
        try: return __channels[channel]
        except: return None

    def __init__(self, channel):

        self.connection = Connection.Connection.get_instance()
        self.name = channel
        
        self.users = {}

        if channel in Channel.__channels:
            self = Channel.__channels[channel]
        elif channel not in Channel.__channels:
            Channel.__channels[channel] = self
    
    def __repr__(self):

        return str(self.name)
    
    def to_s(self):

        return str(self.name)
    
    def is_self(self):

        return False
    
    def message(self, *data):

        for slice in data:
            message = Channel.format_privmsg(self.name, slice)
            self.connection.send(message)

    privmsg = message
    
    def notice(self, data):

        message = Channel.format_notice(self.name, data)
        
        self.connection.send(message)
    
    def set_topic(self, data):

        message = Channel.format_topic(self.name, data)
        
        self.connection.send(message)
    
    def kick(self, user, reason = 'Your behaviour is not conductive to the desired environment'):

        message = Channel.format_kick(self.name, user, reason)
        
        self.connection.send(message)

    def request_who(self):
    
        message = Channel.format_who(self.name)
        
        self.connection.send(message)
    
    def parse_who(self, data):
    
        line = data.message
        
        user = User.find_user(nick = line[2])
        if user is None:
            user = User(nick = line[2], host = line[1])
        user.update_account(account = line[3] if line[3] is not '0' else '*')
        
        user = {    'host'      : line[1],
                    'account'   : line[3] if line[3] is not '0' else '*'}

        if nick in self.users:
            self.users[nick] = user
        else:
            self.users.update({ nick : user })

class Message(Structure):

    def __init__(self, data):

        self.data = data
    
    def __call__(self):

        return self.data.split()
    
    def __repr__(self):

        return str(self.data)
    
    def __eq__(self, (index, cmp)):

        return self.data.split()[index] == cmp
    
    def __ne__(self, (index, cmp)):

        return self.data.split()[index] != cmp
    
    def __len__(self):

        return len(self.data)
    
    def __getitem__(self, index):

        return self.data.split()[index]
    
    def split(self, delim):

        return self.data.split(delim)
        
    def contains(self, value):

        return value in self.to_s()
    
    def has_index(self, index):

        try:
            if self.data.split()[index]:
                return True
            else:
                return False
        except (IndexError):
            return False
    
    def raw(self):

        return self.data
    
    def to_s(self):

        return str(self.data)

class Type(Structure):

    def __init__(self, typedata):

        self.type = typedata
    
    def __repr__(self):

        return str(self.type)
    
    def __call__(self):

        return str(self.type)
    
    def to_s(self):

        return str(self.type)
        
    def to_i(self):

        try: return int(self.type)
        except (ValueError): return self.type

class User(Structure):
    
    users = []
    
    @staticmethod
    def find_userstring(userstring):
    
        for user in User.users:
            user.update_userstring()
            if user.userstring == userstring:
                return user
            continue
    
    @staticmethod
    def find_users(nick = None, ident = None, host = None):
    
        result = []
    
        for user in User.users:
            if nick is not None and nick in user.nick:
                result.append(user)
            if ident is not None and ident in user.ident:
                result.append(user)
            if host is not None and host in user.host:
                result.append(user)
        
        return result
    
    @staticmethod
    def find_user(nick = None, ident = None, host = None):
        """ This method uses User.find_users and performs a best-fit search on the result if more than one is returned. """
        
        result = User.find_users(nick, ident, host)
        
        if len(result) == 1: return result[0]
        elif len(result) == 0: return None
        
        best_match = None
        method = None
        
        for user in User.users:
            if nick is not None and nick is user.nick:
                best_match = user
                method = 'nickname'
            if ident is not None and ident is user.ident:
                best_match = user
                method = 'ident'
            if host is not None and host is user.host:
                best_match = user if best_match is None or method is 'ident' and best_match is user else None
                method = 'hostname'
            if best_match is None: continue

        return best_match

    @staticmethod
    def format_whois(user):
    
        return "WHOIS %s" % (user)

    @staticmethod
    def format_notice(user, message):
    
        return "NOTICE %s :%s" % (user, message)

    @staticmethod
    def format_privmsg(user, message):
    
        return "PRIVMSG %s :%s" % (user, message)

    def __init__(self, userstring = None, nick = None, ident = None, host = None):

        self.connection = Connection.Connection.get_instance()

        if not userstring:
            self.nick = nick
            self.ident = ident
            self.host = host
            self.account = '*'
            
            if self.connection._registered and (ident is None or host is None):
                self.connection.send(User.format_whois(self.nick))
            else:
                self.update_userstring()
        elif userstring:
            self.pattern = re.compile(r"""([^!].+)!(.+)@(.*)""", re.VERBOSE)

            self.userstring = userstring
            try:
                self.nick, self.ident, self.host = self.pattern.match(self.userstring).groups()
            except:
                self.nick = None
                self.ident = None
                self.host = None
                
        dupes = User.find_users(nick = self.nick)
        if len(dupes) > 0:
            for user in dupes:
                User.users.remove(user)

        self.gecos = ''

        User.users.append(self)
    
    def __repr__(self):
    
        self.update_userstring()
        
        return str(self.userstring)
    
    def is_self(self):

        if self.nick == self.connection.nick:
            return True
        else:
            return False
    
    def update_userstring(self):
    
        self.userstring = "%s!%s@%s" % (self.nick, self.ident, self.host)
    
    def update_account(self, account = '*'):
    
        self.account = account
    
    def update_gecos(self, gecos = ''):

        self.gecos = gecos

    def message(self, *data):

        for slice in data:
            message = User.format_privmsg(self.nick, slice)
            self.connection.send(message)
    
    privmsg = message
    
    def notice(self, data):

        message = User.format_notice(self.nick, data)
        
        self.connection.send(message)
    
    def nick_change(self, nick):
    
        self.nick = nick
        
        self.update_userstring()
    
    def quit(self, message = "Quitting."):
    
        users.remove(self)
    
    remove = quit
    
    def to_s(self):

        self.update_userstring()
        
        return self.userstring