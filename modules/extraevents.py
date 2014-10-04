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
                event.bot.botsay('SUB HYPE! PRAISE %s ヽ༼ຈل͜ຈ༽ﾉ' % event.data.split()[0].upper())


    if event.etype == 'msg' and 'http://steamcommumlity.com' in event.data and 'borkedbot' in event.bot.oplist:
        event.bot.botsay(".timeout %s 900000" % event.user)
        event.bot.botsay(".ban %s" % event.user)
        event.bot.botsay("Get rekt idiot spambot.")
