# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import ast, hashlib, htmlentitydefs, inspect, malibu, os, re, signal, sys

from malibu import util
from malibu.util.log import LoggingDriver

__all__ = ['Escapes']

LOG = LoggingDriver.get_logger()

def fork():

    try:
        pid = os.fork()
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)
    if (pid == 0):
        os.setsid()
        # ignore SIGHUP
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
        if (pid == 0):
            os.chdir(os.getcwd())
            os.umask(0)
        else:
            LOG.debug("forking as %d" % (pid))
            LOG.debug("backgrounded from: %s" % (os.getcwd()))
            os._exit(0)
    else:
        os._exit(0)

def fix_unicode(text):

    def sub(match):

        if len(match.group(1)) % 2 == 1:
            return match.group()
        else:
            return ur"%s\%s" % (match.group(1), match.group(2))
    
    ast.literal_eval("'%s'" % re.sub(ur"(\\+)(')", sub, text))

def get_caller():

    frame = inspect.currentframe()
    callstack = inspect.getouterframes(frame, 2)
    caller = callstack[2][0]
    callerinfo = inspect.getframeinfo(caller)
    
    if 'self' in caller.f_locals:
        caller_class = caller.f_locals['self'].__class__.__name__
    else:
        caller_class = None
    
    caller_name = callerinfo[2]
    
    if caller_class:
        caller_string = "%s.%s" % (caller_class, caller_name)
    else:
        caller_string = "%s" % (caller_name)

    return caller_string

def md5(data):

    _m = hashlib.md5()
    _m.update(data)
    return _m.hexdigest()

def unescape(text):

    def fixup(m):

        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)
