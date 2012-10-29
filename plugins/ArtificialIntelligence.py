#!/usr/bin/env python

import os, logging, core, sys, traceback, threading, random
from core import CorePlugin, Event, get_connection, util
from core.util import Escapes
from core.CorePlugin import Plugin
from urllib import urlopen
from random import randint
try:
    import megahal
    has_megahal = True
except ImportError:
    logging.getLogger('ashiema').error("You must install py-megahal to use this plugin.")
    has_megahal = False

get_thread = lambda func, data: threading.Thread(target = func, args = (data,))

class ArtificialIntelligence(Plugin):

    def __init__(self, connection, eventhandler):
    
        Plugin.__init__(self, connection, eventhandler)
        
        self.brain = megahal.MegaHAL(brainfile = os.getcwd() + "/brain")
        self.scheduler = connection.scheduler
        
        self.eventhandler.get_default_events()['MessageEvent'].register(self.handler)
        self.eventhandler.get_default_events()['PluginsLoadedEvent'].register(self._load_identification)
        
        self.connection.tasks.update({
            "ArtificialIntelligence__scheduled_sync" :
                self.scheduler.add_interval_job(
                    self.sync,
                    minutes = 30
                )
            }
        )
        
        # chance (out of 100) that the AI will respond.
        self.response_chance = 30
    
    def __deinit__(self):
    
        self.eventhandler.get_default_events()['MessageEvent'].deregister(self.handler)
        self.eventhandler.get_default_events()['PluginsLoadedEvent'].deregister(self._load_identification)
    
        self.scheduler.unschedule_job(
            self.connection.tasks.pop(
                "ArtificialIntelligence__scheduled_sync"
            )
        )
    
    def _load_identification(self):
    
        self.identification = self.connection.pluginloader.get_plugin("IdentificationPlugin")
    
    def sync(self):
    
        thread = get_thread(self.brain.sync, ())
        thread.setDaemon(True)
        thread.start()
    
    def handler(self, data):
    
        if data.message == (0, '@learn'):
            try:
                url = data.message[1]
            except IndexError:
                data.target.message("%s[AI]%s: %sPlease provide a URL to learn from." % (Escapes.RED, Escapes.WHITE, (Escapes.BOLD + Escapes.AQUA)))
                return
            content = urlopen(url).read().split('\n')
            [self.brain.learn(line) for line in content]
            data.target.message("%s[AI]%s: %sLearned from %s%s%s lines." % (Escapes.RED, Escapes.WHITE, (Escapes.BOLD + Escapes.AQUA), Escapes.LIGHT_BLUE, len(content), (Escapes.BOLD + Escapes.AQUA)))
            self.sync()
        elif data.message == (0, '@chance'):
            assert self.identification.require_level(data, 1)
            try:
                new_chance = int(data.message[1])
            except IndexError:
                data.target.message("%s[AI]%s: Chance is currently set to: %s%s." % (Escapes.RED, Escapes.WHITE, (Escapes.BOLD + Escapes.AQUA), self.response_chance))
                return
            except Exception, e:
                data.target.message("%s[AI]%s: Error setting chance: %s%s" % (Escapes.RED, Escapes.WHITE, (Escapes.BOLD + Escapes.AQUA), e.message))
                return
            self.response_chance = new_chance
            data.target.message("%s[AI]%s: Set chance to %s%s." % (Escapes.RED, Escapes.WHITE, (Escapes.BOLD + Escapes.AQUA), new_chance))
        elif data.message == (0, self.connection.nick + ",") or data.message == (0, self.connection.nick + ":") or data.message == (0, self.connection.nick):
            data.target.message(self.brain.get_reply(data.origin.nick + ", " + data.message[1:]))
        else:
            self.brain.learn(data.message.to_s())
            resp = randint(1, 100)
            if resp < self.response_chance:
                data.target.message(self.brain.get_reply(data.message.to_s()))

__data__ = {
    'name'    : 'ArtificialIntelligence',
    'version' : '1.0',
    'require' : ['IdentificationPlugin'],
    'main'    : ArtificialIntelligence
}