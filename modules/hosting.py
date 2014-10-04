# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import time
import twitchapi

LOAD_ORDER = 40

AUTO_UNHOST = True
WHITELIST = ['monkeys_forever', 'superjoe', 'imayhaveborkedit']

IS_HOSTING = None
HOSTED_CHANNEL = None
LAST_CHECK = None

CHECK_THRESHOLD = 30
OFFLINE_THRESHOLD = 300

def setup(bot):
    pass

def alert(event):
    global AUTO_UNHOST

    if event.etype == 'jtvmsg':
        if 'Only the channel owner and channel editors can use the /unhost command.' in event.data:
            print "[Hosting] Not an editor, cannot unhost."
            AUTO_UNHOST = False

    if event.etype == 'infomsg':
        nowhosting(event)
        checkifhostonline(event)


def nowhosting(event):    
    global IS_HOSTING
    global HOSTED_CHANNEL

    if event.data.startswith('HOSTTARGET') and event.data.split()[1] != '-':
        IS_HOSTING = True
        HOSTED_CHANNEL = event.data.split()[1]
        streamdata = twitchapi.get('streams/%s' % HOSTED_CHANNEL, 'stream')
        
        print '[Hosting] WE ARE NOW HOSTING %s' % HOSTED_CHANNEL

        if streamdata:
            event.bot.botsay("Now hosting %s, playing %s.  All %s of you, go check it out! %s" % 
                (HOSTED_CHANNEL, str(streamdata['game']), event.data.split()[2],'http://twitch.tv/%s' % HOSTED_CHANNEL))
        else: 
            print "[Hosting] %s is not streaming." % HOSTED_CHANNEL
    elif event.data.startswith('HOSTTARGET') and event.data.split()[1] == '-':
        print "[Hosting] Unhosting %s " % HOSTED_CHANNEL

        IS_HOSTING = False
        HOSTED_CHANNEL = None


def checkifhostonline(event):
    if IS_HOSTING and AUTO_UNHOST and event.channel in WHITELIST:
        global LAST_CHECK

        if LAST_CHECK is None:
            LAST_CHECK = time.time()

        elif time.time() - LAST_CHECK > CHECK_THRESHOLD:
            streamdata = twitchapi.get('streams/%s' % HOSTED_CHANNEL, 'stream')

            if streamdata:
                LAST_CHECK = time.time()
            elif time.time() - LAST_CHECK > OFFLINE_THRESHOLD:
                print "[Hosting] %s has been offline for long enough, attempting to unhost" % HOSTED_CHANNEL
                event.bot.botsay('/unhost')
