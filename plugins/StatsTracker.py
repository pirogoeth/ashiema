#!/usr/bin/env python2.7

from core import Plugin, Events, util
from core.util import Escapes
from core.Plugin import Plugin
from core.HelpFactory import Contexts, CONTEXT, DESC, PARAMS, ALIASES

class StatsTracker(Plugin):

    def __init__(self):
    
        Plugin.__init__(self, needs_dir = False, needs_comm_pipe = False)
        
        self._db = {}
        self._db.update({ 'channels'  : {} })

        self.get_event('MessageEvent').register(self.handler)
        
        self.connection.tasks.update({
            "StatsTracker__reset_weekly":
                self.scheduler.add_interval_job(
                    self.__weekly_clean,
                    days = 7
                )
            }
        )
    
    def __deinit__(self):
    
        self.get_event('MessageEvent').deregister(self.handler)
        
        [self.scheduler.unschedule_job(self.connection.tasks.pop(task))
            for task in ["StatsTracker__reset_weekly"]]

    def __weekly_clean(self):
    
        self._db['channels'].clear()
        self._db['totals'].clear()
        
        # eventually, print out the final stats here to the log.
        
        self.log_info('Stats have been cleared!')

    def handler(self, data):
    
        if data.message == (0, '@stats'):
            channel, user = data.target.to_s(), data.origin.to_s()
            if channel not in self._db['channels']:
                self._db['channels'].update({ channel : {} })
                data.origin.notice("%s[StatsTracker]: There are no stats available." % (Escapes.AQUA))
                return
            if user not in self._db['channels'][channel]:
                self._db['channels'][channel].update({ user : (0, 0, 0) })
                data.origin.notice("%s[StatsTracker]: You have no stats for %s." % (Escapes.AQUA, channel))
            stats = []
            for channel, users in self._db['channels'].iteritems():
                if user in users:
                    stat = users[user]
                    stats.append(stat)
                    data.origin.notice("%s[StatsTracker]: Stats for %s%s%s: word count => %s, character count => %s, line count => %s" % (Escapes.AQUA, Escapes.BOLD, channel, Escapes.BOLD, stat[0], stat[1], stat[2]))
            stats = [sum(set) for set in zip(*stats)]
            data.origin.notice("%s[StatsTracker]: Total stats: word count => %s, character count => %s, line count => %s" % (Escapes.AQUA, stats[0], stats[1], stats[2]))
        elif data.message == (0, '@chanstats'):
            channel, user = data.target.to_s(), data.origin.to_s()
            if channel not in self._db['channels']:
                self._db['channels'].update({ channel : {} })
                data.target.privmsg("%s[StatsTracker]: There are no channel stats available." % (Escapes.AQUA))
                return
            try: stat_set = self._db['channels'][channel].values()
            except: 
                data.target.privmsg("%s[StatsTracker]: An error occurred while gathering statistics." % (Escapes.AQUA))
            stats = [sum(set) for set in zip(*stat_set)]
            data.target.message("%s[StatsTracker]: Stats for %s%s%s:" % (Escapes.AQUA, Escapes.BOLD, channel, Escapes.BOLD),
                                "   Word count: %s" % (stats[0]),
                                "   Character count: %s" % (stats[1]),
                                "   Line count: %s" % (stats[2]))
        else:
            channel, user = data.target.to_s(), data.origin.to_s()
            if channel not in self._db['channels']:
                self._db['channels'].update({ channel : {} })
            if user not in self._db['channels'][channel]:
                self._db['channels'][channel].update({ user : (0, 0, 0) })
            wc, cc = len(data.message.split(' ')), len(data.message)
            stat = (self._db['channels'][channel][user][0] + wc, self._db['channels'][channel][user][1] + cc, self._db['channels'][channel][user][2] + 1)
            self._db['channels'][channel][user] = stat

__data__ = {
    'name'      : 'StatsTracker',
    'version'   : '1.0',
    'require'   : [],
    'main'      : StatsTracker,
    'events'    : []
}

__help__ = {
    '@stats' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Calculates user statistics per-channel and total, notices them to the user.',
        PARAMS  : '',
        ALIASES : []
    },
    '@chanstats' : {
        CONTEXT : Contexts.PUBLIC,
        DESC    : 'Prints total channel statistics, displays to channel.',
        PARAMS  : '',
        ALIASES : []
    }
}