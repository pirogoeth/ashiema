import os, logging, sys, signal

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

""" these are some various utilities needed for use in the startup process and other parts of runtime """

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
            logging.getLogger('ashiema').debug("forking as %d" % (pid))
            logging.getLogger('ashiema').debug("backgrounded from: %s" % (os.getcwd()))
            os._exit(0)
    else:
        os._exit(0)