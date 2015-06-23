# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013-2015 Sean Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import ashiema, collections, malibu, re, traceback

from ashiema.irc.eventhandler import EventHandler

from malibu.util.log import LoggingDriver

LOG = LoggingDriver.find_logger()


class Token(object):
    """ Uses a set of regexes to split up a line and turn each matched group (Origin, Type, Target, Message)
        into tokens that makes usage, responding, and formatting much easier. """

    @staticmethod
    def process_events(data):
        """ Passes +data+ to the EventHandler's event mapper for processing.
        """

        EventHandler.get_instance().map_events(data)

    def __init__(self, connection, data):
        """ Tokenizes +data+ according to a regex and matches each group with the proper structure based on content.
        """

        self.connection = connection
        self._raw = data

        # this regular expression splits an IRC line up into four parts:
        # ORIGIN, TYPE, TARGET, MESSAGE
        proto_regex = r"^(?:\:([^\s]+)\s)?([A-Za-z0-9]+)\s(?:([^\s\:]+)\s)?(?:\:?(.*))?$"
        user_regex = r"([\w\d\-_]+\![~\w\d\-_]+\@[\w\d\-_.]+)"

        # a regular expression to match and dissect IRC protocol messages
        # this is around 60% faster than not using a RE
        proto_p = re.compile(proto_regex, re.VERBOSE)
        user_p = re.compile(user_regex, re.VERBOSE)

        try:
            self.origin, self.type, self.target, self.message = (None, None, None, None)
            self._origin, self._type, self._target, self._message = proto_p.match(data).groups()
            # take each token and initialise the appropriate structure.

            try:
                if len(user_p.findall(self._origin)) == 0:
                    self.origin = Origin(self, self._origin) if self._origin is not None else None
                else:
                    self.origin = User.find_userstring(self._origin)
                    if not self.origin:
                        self.origin = User(self, userstring = self._origin)
            except: self.origin = None

            self.type = Type(self, self._type) if self._type is not None else None

            if self._target is None:
                pass
            elif self._target.startswith('#', 0, 1) is True:
                self.target = Channel(self, self._target)
            else:
                if self._target == '*':
                    self.target = self._target
                else:
                    try: self.target = User.find_user(nick = self._target)
                    except:
                        self.target = User(self, nick = self._target)
            self.message = Message(self, self._message)
        except (AttributeError):
            pass
        except:
            [LoggingDriver.find_logger().error(trace)
             for trace in traceback.format_exc(5).split('\n')]
            pass

    def get_raw(self):
        """ Returns the raw, untokenized data that was received from the server.
        """

        return self._raw

    def respond_to_user(self, message, prefer_notice = True):
        """ Determines the best way to respond to the user and sends +message+ that way.
            If +prefer_notice+ is true, the message will be sent as a NOTICE instead of a
            PRIVMSG.
        """

        if self.target.is_self():
            if prefer_notice:
                self.origin.notice(message)
            else:
                self.origin.message(message)
        else:
            self.target.message(message)

