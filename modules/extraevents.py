# -*- coding: utf-8 -*-
import twitchapi

def setup(bot):
    pass

def alert(event):
    if event.etype == 'twitchnotify':
        if 'just subscribed!' in event.data:
            event.bot.say(event.channel, 'ヽ༼ຈل͜ຈ༽ﾉ SUB HYPE! PRAISE %s ヽ༼ຈل͜ຈ༽ﾉ' % event.data.split()[0].upper())

        if event.data.startswith('HOSTTARGET') and event.data.split()[1] != '-':
        	hs = event.data.split()[1]
        	sr = twitchapi.get('streams/%s' % hs, 'stream')
        	if not sr:
        		event.bot.say(event.channel, "Now hosting %s, playing %s.  Go check it out! %s" % 
        			(hs, str(sr['game']), 'http://twitch.tv/%s' % hs))
        	else: 
        		print "%s is not streaming." % hs
    	# add hosting event "Now hosting %channel, playing $game"