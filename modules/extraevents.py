# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import os, time, json, random

LOAD_ORDER = 30


def setup(bot):
    pass

def alert(event):
    # Sub alert
    if event.etype == 'twitchnotify':
        if event.channel in ['unsanitylive', 'monkeys_forever', 'superjoe', 'kizzmett']:
            if 'just subscribed!' in event.data:
                extra = ''
                if event.channel == 'monkeys_forever':
                    extra = ' | If you want an invite to the sub guild use !guildinvite steamid'

                event.bot.botsay('ヽ༼ຈل͜ຈ༽ﾉ SUB HYPE! PRAISE %s%s' % (event.data.split()[0].upper(), extra))
