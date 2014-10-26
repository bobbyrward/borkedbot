# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import os, time, json, random
import twitchapi, steamapi, settings

LOAD_ORDER = 30

def setup(bot):
    pass

def alert(event):
    # Sub alert
    if event.etype == 'twitchnotify':
        if event.channel in ['unsanitylive', 'monkeys_forever', 'superjoe', 'kizzmett']:
            if 'just subscribed!' in event.data:
                event.bot.botsay('ヽ༼ຈل͜ຈ༽ﾉ SUB HYPE! PRAISE %s' % event.data.split()[0].upper())


    if event.etype == 'msg' and 'borkedbot' in event.bot.oplist:
        if 'http://steamcommumlity.com' in event.data:
            event.bot.botsay(".timeout %s 900000" % event.user)
            event.bot.botsay(".ban %s" % event.user)
            event.bot.botsay("Get rekt idiot spambot.")
            print '[Extra Events] Banning %s' % event.user

        if event.user.startswith('scorpionx'):
            event.bot.botsay(".timeout %s 900000" % event.user)
            event.bot.botsay(".ban %s" % event.user)
            event.bot.botsay("Pls no")
            print '[Extra Events] Banning %s' % event.user

        if '░' in event.data:
            event.bot.botsay(".timeout %s 10" % event.user)