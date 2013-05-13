#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, sys, re, cgi, wsgiref
from core import Plugin, Event, get_connection, util
from core.util import Escapes, unescape
from core.Plugin import Plugin
from contextlib import closing
from cgi import parse_qs, escape
from wsgiref.simple_server import make_server

class HTTPServer(Plugin):
    pass

class HTTPResponseHandler(object):
    pass

class HTTPResponseEvent(Event):
    pass

class Templating(object):

    """ This is a template parsing class, which will be used in conjunction with ashiema's HTTP server to serve templated
        HTML pages that have the ability to provide plugin-specific information.  By default, templating will work as follows:
        
        Interpolation:
            %{ statement; }
        
            Interpolation applies to variables and statements, so input from anything can be used in-line.
        
        Flow Control:
            = if whatever is something or something is None
              do things...
            = else
              do something else..
            back to first level content.
            
            Flow control blocks use indentation to determine when to break into a separate block.
            
            = for item in items
              ...
            
            = while some_condition
              ...
    """
    
    def __init__(self,
                 interpolation_regex = re.compile(r"%\{([^%\{|\}]+)\}", re.VERBOSE),
                 block_regex = re.compile(r"(?:\s+)?=\s+?([^%\{\}\r\n]+):?", re.VERBOSE),
                 preprocessor = (lambda data, option: data.lstrip()),
                 globals_dict = {},
                 exc_handle = None):

        # regexes for matching template statements        
        self.interpol_regex = interpolation_regex
        self.block_regex = block_regex
        
        # function used to process data before handling it
        self.preprocessor = preprocessor
        
        # function that handles exceptions
        self.exc_handler = exc_handle if exc_handle is not None else self.__exc_handle__
        
        # variables to make available to the scope of the templated page
        self.globals = globals_dict
        self.locals = { '_parse': self._parseblock_ }
        
        # keywords that are allowed to be used to lead blocks
        self.allowed_blocks = ['for', 'while', 'if', 'elif', 'else']
        
        # the two types of whitespace we care about
        self._space = " "
        self._tab = "\t"
        
        # options
        self.__options = {
            'indent_type'           : 's', # type of indents, 's' for spaces, 't' for tabs
            'block_indent_size'     : 2, # size of the content indent inside blocks
            'block_char'            : '=', # character used to mark beginning of a block, same that is given in the regex
            'debugging'             : False, # do i print debugging information?
            'input'                 : sys.stdin, # alternate input if `block` is not given to +parse()+
            'output'                : sys.stdout # output for parsed data
        }
    
    def __exc_handle__(self, exc_str):

        raise Exception(exc_str)
        
    def _count_whitespace_(self, statement):
    
        if self.options()['indent_type'].lower() == 's':
            return len(statement) - len(statement.lstrip(self._space))
        elif self.options()['indent_type'].lower() == 't':
            return len(statement) - len(statement.lstrip(self._tab))
        else:
            self.options()['indent_type'] = 's'
            return self._count_whitespace_(statement)
    
    def _parseblock_(self, pos = 0, last_pos = None):

        def repl(match, self = self):
            expr = self.preprocessor(match.group(1), 'eval')
            try: return str(eval(expr, self.globals, self.locals))
            except: return str(self.exc_handler(expr))
        
        block = self.locals['_block']

        if last_pos is None:
            last_pos = len(block)
        
        while pos < last_pos:
            line = block[pos]
            match = self.block_regex.match(line)
            if match:
                stmt = match.group(1)
                if self.options()['debugging']:
                    print "matched: [" + stmt + "] from line: {" + line + "}, indent size: " + str(line.index(self.options()['block_char']))
                eind_size = line.index(self.options()['block_char'])
                eind_size += self.options()['block_indent_size']
                search = pos + 1
                nest = 1
                while search < last_pos:
                    line = block[search]
                    ind_size = self._count_whitespace_(line)
                    if ind_size >= eind_size: # we have an indentation after our block
                        search += 1
                    else:
                        nest -= 1
                        if nest == 0:
                            break
                stmt = self.preprocessor(stmt, 'exec')
                if self.options()['debugging']:
                    print "executing statement: [" + stmt + "]" # debug
                if search - (pos + 1) == 0:
                    stmt = '%s' % stmt
                else:
                    if stmt[len(stmt) - 1] != ':':
                        stmt += ':'
                    stmt = '%s _parse(%s, %s)' % (stmt, pos + 1, search)
                exec stmt in self.globals, self.locals
                pos = search
            else:
                self.options()['output'].write(self.interpol_regex.sub(repl, line) + "\n")
                pos += 1

    def options(self):
        
        return self.__options

    def parse(self, block = None):
        
        if block is None:
            block = self.options()['input'].readlines()
        
        self.locals['_block'] = block
        
        self._parseblock_()
