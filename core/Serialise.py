#!/usr/bin/env python

import re, structures, logging, traceback
from structures import Channel, Type, User

class Serialise(object):
    """ convert a line into a fielded object """
    def __init__(self, data):
        self._raw = data
        # this regular expression splits an IRC line up into four parts:
        # ORIGIN, TYPE, TARGET, MESSAGE
        regex = "^(?:\:([^\s]+)\s)?([A-Za-z0-9]+)\s(?:([^\s\:]+)\s)?(?:\:?(.*))?$"
        # a regular expression to match and dissect IRC protocol messages
        # this is around 60% faster than not using a RE
        p = re.compile(regex, re.VERBOSE)
        try:
            self.origin, self.type, self.target, self.message = (None, None, None, None)
            self._origin, self._type, self._target, self.message = p.match(data).groups()
            # turn each serialisable field into an object
            self.origin = User.User(self._origin) if self._origin is not None else None
            self.type = Type.Type(self._type) if self._type is not None else None
            if self._target.startswith('#', 0, 1) is True:
                self.target = Channel.Channel(self._target) if self._target is not None else None
            else: self.target = User.User(self._target) if self._target is not None else None
        except (AttributeError):
            pass
        try:
            if logging.getLogger('ashiema').getEffectiveLevel() is 10:
                logging.getLogger('ashiema').debug("%s %s %s %s" % (str(self.origin), str(self.type), str(self.target), str(self.message)))
        except:
            [logging.getLogger('ashiema').error(trace) for trace in traceback.format_exc(5).split('\n')]
            pass
    
    def print_raw(self):
        print self._raw