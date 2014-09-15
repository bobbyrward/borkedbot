# -*- coding: utf-8 -*-


def setup(bot):
    pass

def alert(event):
    if event.etype == 'twitchnotify':
        if 'has just subscribed!' in event.data:
            bot.botsay('ヽ༼ຈل͜ຈ༽ﾉ NEW SUB HYPE ヽ༼ຈل͜ຈ༽ﾉ')
