# -*- coding: utf-8 -*-


def setup(bot):
    pass

def alert(event):
    if event.etype == 'twitchnotify':
        if 'just subscribed!' in event.data:
            event.bot.botsay('ヽ༼ຈل͜ຈ༽ﾉ SUB HYPE! PRAISE %s ヽ༼ຈل͜ຈ༽ﾉ' % event.data.split()[0].upper())
