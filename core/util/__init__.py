import os, re, logging, sys, signal, htmlentitydefs

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

""" these are some various utilities needed for use in the startup process and other parts of runtime """

def fork(forkpty = False):
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
            logging.getLogger('ashiema').debug("forking as %d" % (pid))
            logging.getLogger('ashiema').debug("backgrounded from: %s" % (os.getcwd()))
            os._exit(0)
    else:
        os._exit(0)
    if forkpty:
        return os.forkpty()
    else:
        return ()

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