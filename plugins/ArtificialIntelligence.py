#!/usr/bin/env python

# ashiema: a lightweight, modular IRC bot written in python.
# Copyright (C) 2013 Shaun Johnson <pirogoeth@maio.me>
#
# An extended version of the license is included with this software in `ashiema.py`.

import os, logging, ashiema, sys, traceback, threading, random
from ashiema import Plugin, Events, HelpFactory, util
from ashiema.util import Escapes
from ashiema.Plugin import Plugin
from ashiema.HelpFactory import Contexts
from ashiema.HelpFactory import CONTEXT, DESC, PARAMS, ALIASES
from urllib import urlopen
from random import randint
from datetime import timedelta
try:
    import megahal
    has_megahal = True
except ImportError:
    logging.getLogger('ashiema').error("You must install py-megahal to use this plugin.")
    has_megahal = False

class ArtificialIntelligence(Plugin):

    def __init__(self):
    
        Plugin.__init__(self, needs_dir = True)
        
        self.brain = megahal.MegaHAL(brainfile = self.get_path() + "/brain")
        
        self.get_event("MessageEvent").register(self.handler)
        self.get_event("PluginsLoadedEvent").register(self._load_identification)
        
        self.ignored = []
        # chance (out of 100) that the AI will respond (per-channel).
        self.response_chances = {}
        self.default_chance = 30
        
        self.__sync_job = self.scheduler.create_job(
            "ArtificialIntelligence__scheduled_sync", self.sync, timedelta(minutes = 30), recurring = True)

    def __deinit__(self):
    
        self.get_event("MessageEvent").deregister(self.handler)
        self.get_event("PluginsLoadedEvent").deregister(self._load_identification)
    
        self.scheduler.remove_job(self.__sync_job)
    
    def _load_identification(self):
    
        self.identification = self.get_plugin("IdentificationPlugin")
    
    def sync(self):
    
        self.brain.sync()
    
    def handler(self, data):
    
        # set up the chance for a channel if the chance is not already set to prevent errors
        if data.target.to_s() not in self.response_chances:
            self.response_chances[data.target.to_s()] = self.default_chance

        if data.message == (0, '@learn'):
            assert self.identification.require_level(data, 1)
            try:
                url = data.message[1]
            except IndexError:
                data.target.message("%s[AI]%s: %sPlease provide a URL to learn from." % (Escapes.RED, Escapes.BLACK, (Escapes.BOLD + Escapes.AQUA)))
                return
            content = urlopen(url).read().split('\n')
            for line in content:
                if line is '':
                    continue
                else:
                    self.brain.learn(line)
            data.target.message("%s[AI]%s: %sLearned from %s%s%s lines." % (Escapes.RED, Escapes.BLACK, (Escapes.BOLD + Escapes.AQUA), Escapes.LIGHT_BLUE, len(content), (Escapes.BOLD + Escapes.AQUA)))
            self.sync()
        elif data.message == (0, '@chance'):
            assert self.identification.require_level(data, 1)
            try:
                new_chance = int(data.message[1])
            except IndexError:
                data.target.message("%s[AI]%s: Chance is currently set to: %s%s." %
                    (Escapes.RED, Escapes.BLACK, (Escapes.BOLD + Escapes.AQUA), self.response_chances[data.target.to_s()]))
                return
            except Exception, e:
                data.target.message("%s[AI]%s: Error setting chance: %s%s" % (Escapes.RED, Escapes.BLACK, (Escapes.BOLD + Escapes.AQUA), e.message))
                return
            self.response_chances[data.target.to_s()] = new_chance
            data.target.message("%s[AI]%s: Set chance to %s%s." % (Escapes.RED, Escapes.BLACK, (Escapes.BOLD + Escapes.AQUA), new_chance))
        elif data.message == (0, '@ignore'):
            assert self.identification.require_level(data, 1)
            if data.target.to_s() in self.ignored:
                self.ignored.remove(data.target.to_s())
                data.target.message("%s[AI]%s: No longer ignoring %s." % (Escapes.RED, Escapes.BLACK, data.target.to_s()))
            elif data.target.to_s() not in self.ignored:
                self.ignored.append(data.target.to_s())
                data.target.message("%s[AI]%s: Ignoring %s." % (Escapes.RED, Escapes.BLACK, data.target.to_s()))
        elif data.message == (0, self.connection.nick + ",") or data.message == (0, self.connection.nick + ":") or data.message == (0, self.connection.nick):
            if data.target.to_s() in self.ignored:
                return
            data.target.message(self.brain.get_reply(data.origin.nick + ", " + ' '.join(data.message[1:])))
        else:
            if data.target.to_s() in self.ignored:
                return
            self.brain.learn(data.message.to_s())
            resp = randint(1, 100)
            if resp < self.response_chances[data.target.to_s()]:
                data.target.message(self.brain.get_reply(data.message.to_s()))

__data__ = {
    'name'    : 'ArtificialIntelligence',
    'version' : '1.0',
    'require' : ['IdentificationPlugin'],
    'main'    : ArtificialIntelligence,
    'events'  : []
}

__help__ = {
    '@learn'    : {
        CONTEXT   : Contexts.PUBLIC,
        DESC      : 'Allows you to provide a URL to teach the AI from.',
        PARAMS    : '<url>'
    },
    '@chance'   : {
        CONTEXT   : Contexts.PUBLIC,
        DESC      : 'Allows you to check or set chance of the AI replying per-channel. Leave blank to see current chance.',
        PARAMS    : '[chance (out of 100)]'
    },
    '@ignore'   : {
        CONTEXT   : Contexts.PUBLIC,
        DESC      : 'Allows you to keep the AI from learning and replying in a specific channel.',
        PARAMS    : ''
    }
}