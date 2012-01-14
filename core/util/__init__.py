import os, sys, signal

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
            print "\x0aforking as %d" % (pid)
            print 'backgrounded from: %s\x0a' % (os.getcwd())
            os._exit(0)
    else:
        os._exit(0)