# -*- coding: utf-8 -*-
import twitchapi

def setup(bot):
    pass

def alert(event):
    if event.etype == 'twitchnotify':
        if event.channel in ['monkeys_forever', 'superjoe']:
            if 'just subscribed!' in event.data:
                event.bot.say(event.channel, 'SUB HYPE! PRAISE %s ヽ༼ຈل͜ຈ༽ﾉ' % event.data.split()[0].upper())