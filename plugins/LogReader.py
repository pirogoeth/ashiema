# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013-2015 Sean Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import ashiema, datetime, malibu, os, sys, traceback
import errno, multiprocessing, shelve

from ashiema.api.events import Event
from ashiema.api.help import Contexts, CONTEXT, DESC, PARAMS, ALIASES
from ashiema.api.plugin import Plugin
from ashiema.irc.structures import Channel
from ashiema.util import md5, Escapes, unescape

from multiprocessing import Process


class LogReader(Plugin):

    """ This is a faux-threaded plugin that reads all the files defined in a list
        and reports content into a specified channel. Useful for tracking system logs and watching
        for break-in attempts. """
    
    def __init__(self):
    
        Plugin.__init__(self, needs_dir = True, needs_comm_pipe = True)
        
        LogReader.reading = False
        
        self.config = self.get_plugin_configuration()
        
        self.filters = {}
        self.__process = None
        
        if len(self.config) == 0:
            raise Exception("You must configure options for the log watcher (LogReader) in your configuration!")
        
        self.channel = self.config['channel']
        self.files = self.config['files'].split(',')
        
        self.get_event("MessageEvent").register(self.handler)
        self.get_event("PluginsLoadedEvent").register(self.__on_plugins_loaded)
        
        self.__load_filters__()
    
    def __deinit__(self):
    
        self.get_event("MessageEvent").deregister(self.handler)
        self.get_event("PluginsLoadedEvent").deregister(self.__on_plugins_loaded)
        
        self.__stop()

        self.__unload_filters__()
    
    def __load_filters__(self):
    
        try:
            self.shelf = shelve.open(self.get_path() + 'filters.db', flag = 'c', protocol = 0, writeback = True)
            self.filters.update(self.shelf)
        except Exception as e:
            self.filters = None
            [LoggingDriver.find_logger().error(trace) for trace in traceback.format_exc(4).split('\n')]
    
    def __unload_filters__(self):
    
        if self.filters is not None and self.shelf is not None:
            self.shelf.update(self.filters)
            self.shelf.sync()
            self.shelf.close()

    def __on_plugins_loaded(self):
    
        self.identification = self.get_plugin("IdentificationPlugin")
    
        self.__start()
    
    def __start(self):
    
        if LogReader.reading:
            return
        
        LogReader.reading = True
        
        self.__begin_read(self.files)
    
    def __begin_read(self, file_list):
    
        class LogFilter(object):

            def __init__(self, plugin, channel, filters):

                self.plugin = plugin
                self.channel = channel
                self.filters = filters

            def process(self, line):

                term, instruction, data = None, None, None

                for _term, _instruction in self.filters.iteritems():
                    if _term in line:
                        term, instruction = _term, _instruction.upper()
                        break
                    continue

                if instruction == "IGNORE":
                    data = None
                elif instruction == "MARK":
                    data = Channel.format_privmsg(self.channel, "%s%s" % (Escapes.BOLD, line))
                elif instruction == "WARNING":
                    data = Channel.format_privmsg(self.channel, "%s%s" % (Escapes.RED, line))
                elif instruction == "IMPORTANT":
                    data = Channel.format_privmsg(self.channel, "%s%s%s" % (Escapes.BOLD, Escapes.RED, line))
                elif instruction == "NONE":
                    data = Channel.format_privmsg(self.channel, "%s" % (line))
                elif term is not None and instruction is not None: #invalid filter term matched
                    self.plugin.log_info("Invalid filter instruction '%s' matched in the following line:" % (term), "  " + line)
                    index = line.find(term)
                    if index == -1:
                        data = Channel.format_privmsg(self.channel, line)
                    else:
                        line = line[0:index] + Escapes.YELLOW + line[index:(index + len(term))] + Escapes.BLACK + line[(index + len(term)):]
                        data = Channel.format_privmsg(self.channel, line)
                elif term is None and instruction is None: # no filter term matched
                    data = Channel.format_privmsg(self.channel, line)
                
                if data is None:
                    return
                else:
                    self.plugin.push_data(data)

        class LogReaderProcess(Process):
        
            def __init__(self, plugin, channel, files):

                Process.__init__(self, name = "ashiema log reader sub-process")

                self.plugin = plugin
                self.paths = files
                self.files = {}
                self.channel = channel
                self.filters = self.plugin.filters
                self.filter = LogFilter(self.plugin, self.channel, self.filters)
                
                self.open()
            
            def __get_fid__(self, fst):
            
                if os.name == 'posix':
                    return "%xg%x" % (fst.st_dev, fst.st_ino)
                else:
                    return "%f" % (fst.st_ctime)
            
            def __get_st__(self, file):
            
                try:
                    return os.stat(file.name)
                except EnvironmentError as err:
                    if err.errno == errno.ENOENT:
                        self.__close__(file)
            
            def __open__(self, path):
            
                assert os.path.exists(os.path.realpath(path))
                try:
                    fobj = open(path, 'rb')
                    fid = self.__get_fid__(self.__get_st__(fobj))
                    fobj.seek(0, 2)
                    self.files.update({fid : fobj})
                    return fid
                except IOError as err:
                    self.plugin.log_error("An error occurred while trying to open '%s': %s" % (path, err.errno))                    
            
            def __close__(self, fid):
            
                fobj = self.files.pop(fid)
                fobj.close()
            
            def __reload__(self, fid):
            
                path = self.files[fid].name
                self.plugin.log_info("Reloading log file '%s'." % (path))
                self.__close__(fid)
                return self.__open__(path)
            
            def set_active(self, active):

                self.active = active
            
            def open(self):

                for file in self.paths:
                    self.__open__(file)
            
            def read(self):

                for fid in self.files.keys():
                    if fid != self.__get_fid__(self.__get_st__(self.files[fid])):
                        # print fid, self.__get_fid__(self.__get_st__(self.files[fid])) # debug
                        fid = self.__reload__(fid)
                    file = self.files[fid]
                    file.seek(file.tell())
                    for line in file:
                        self.filter.process(line)
            
            def close(self):

                for fid in self.files.keys():
                    self.__close__(fid)
            
            def run(self):

                self.active = True
                while self.active:
                    try:
                        time.sleep(0.00025)
                        self.read()
                    except (SystemExit, KeyboardInterrupt) as e:
                        self.close()
                        return
                self.close()
        
        self.__process = LogReaderProcess(self, self.channel, self.files)
        self.__process.start()
        self.log_info("Started log monitor in child process [PID: %s]." % (self.__process.pid))
    
    def __stop(self):
    
        if not LogReader.reading:
            return
        
        LogReader.reading = False
        
        self.log_info("Deactivating log monitor...")
        self.__process.set_active(False)

        self.log_info("Terminating child process...")
        self.__process.terminate()
    
    def __restart(self):
    
        if not LogReader.reading:
            self.log_error("Can't restart, log monitor is not running.")
            return
        
        self.__stop()
        
        self.log_info("Restarting log monitor...");
        
        self.__start()
    
    def handler(self, data):
        
        if data.message == (0, "@log-filter"):
            assert self.identification.require_level(data, 2)
            term, instruction = None, None
            try:
                if len(data.message[1:]) >= 2:
                    instruction = data.message[1]
                    term = ' '.join(data.message[2:])
                    self.filters.update({term : instruction})
                    data.respond_to_user("Log filtering has been enabled for term: '%s'" % (term))
                    data.respond_to_user("Action taken when term is matched: %s" % (self.filters[term].upper()))
                    self.__restart()
                elif len(data.message[1:]) == 1:
                    term = data.message[1]
                    if term in self.filters:
                        data.respond_to_user("Log filtering is enabled for term: %s" % (term))
                        data.respond_to_user("Action taken when term is matched: %s" % (self.filters[term].upper()))
                        return
                    else:
                        data.respond_to_user("Log filtering is %sNOT%s enabled for term: %s" % (Escapes.RED, Escapes.BLACK, term))
                        return
                elif len(data.message()) == 1:
                    if len(self.filters) > 0:
                        data.respond_to_user("Enabled log filters:")
                        for term, instruction in self.filters.iteritems():
                            data.respond_to_user("  '%s%s%s' => %s" % (Escapes.BOLD, term, Escapes.BLACK, instruction))
                    else:
                        data.respond_to_user("There are no log filters set.")
            except Exception as e:
                [self.log_info(line) for line in traceback.format_exc(4).split("\n")]
        elif data.message == (0, "@clear-log-filter"):
            assert self.identification.require_level(data, 2)
            term = None
            try:
                term = ' '.join(data.message[1:])
                if term in self.filters:
                    del self.filters[term]
                    data.respond_to_user("Cleared filter for term '%s'." % (term))
                    self.__restart()
                else:
                    data.respond_to_user("There is no filter set for '%s'." % (term))
            except IndexError as e:
                data.respond_to_user("You must provide a term to clear.")
                return
            except Exception as e:
                [self.log_info(line) for line in traceback.format_exc(4).split("\n")]
            
__data__ = {
    'name'      : 'LogReader',
    'main'      : LogReader,
    'version'   : '1.0',
    'require'   : ['IdentificationPlugin'],
    'events'    : []
}

__help__ = {
    '@log-filter' : {
        CONTEXT : Contexts.BOTH,
        DESC    : 'Adds or prints information about a log filter, or lists all enabled log filters.',
        PARAMS  : '[filter instruction, one of IGNORE, MARK, WARNING, IMPORTANT] [filter term]',
        ALIASES : []
    },
    '@clear-log-filter' : {
        CONTEXT : Contexts.BOTH,
        DESC    : 'Removes a log filter from the database',
        PARAMS  : '[filter term]',
        ALIASES : []
    }
}
    
