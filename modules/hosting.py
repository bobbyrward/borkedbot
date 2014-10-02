# -*- coding: utf-8 -*-
import twitchapi, time

AUTO_UNHOST = True
WHITELIST = ['monkeys_forever', 'superjoe', 'imayhaveborkedit']

IS_HOSTING = None
HOSTING_CHANNEL = None
LAST_CHECK = None

CHECK_THRESHOLD = 30
OFFLINE_THRESHOLD = 300

def setup(bot):
    pass

def alert(event):
    global AUTO_UNHOST

    if event.etype == 'jtvmsg':
        if 'Only the channel owner and channel editors can use the /unhost command.' in event.data:
            print "Not an editor, cannot unhost."
            AUTO_UNHOST = False

        nowhosting(event)
        checkifhostonline(event)


def nowhosting(event):    
    global IS_HOSTING
    global HOSTING_CHANNEL

    if event.data.startswith('HOSTTARGET') and event.data.split()[1] != '-':
        hostedstreamer = event.data.split()[1]
        streamdata = twitchapi.get('streams/%s' % hostedstreamer, 'stream')
        
        IS_HOSTING = True
        HOSTING_CHANNEL = hostedstreamer
        
        if streamdata:
            event.bot.say(event.channel, "Now hosting %s, playing %s.  All %s of you, go check it out! %s" % 
                (hostedstreamer, str(streamdata['game']), event.data.split()[2],'http://twitch.tv/%s' % hostedstreamer))
        else: 
            print "%s is not streaming." % hostedstreamer
    elif event.data.startswith('HOSTTARGET') and event.data.split()[1] == '-':
        IS_HOSTING = False
        HOSTING_CHANNEL = None
        print "Unhosting"


def checkifhostonline(event):
    if IS_HOSTING and AUTO_UNHOST and event.channel in WHITELIST:
        global LAST_CHECK

        if LAST_CHECK is None:
            LAST_CHECK = time.time()
        
        elif time.time() - LAST_CHECK > CHECK_THRESHOLD:
            streamdata = twitchapi.get('streams/%s' % HOSTING_CHANNEL, 'stream')

            if streamdata:
                LAST_CHECK = time.time()
            elif time.time() - LAST_CHECK > OFFLINE_THRESHOLD:
                print "[Hosting] %s has been offline for long enough, attempting to unhost" % HOSTING_CHANNEL
                event.bot.say(event.channel, '/unhost')
