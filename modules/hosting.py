# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import time
import twitchapi, settings

LOAD_ORDER = 40

WHITELIST = ['monkeys_forever', 'superjoe', 'imayhaveborkedit', 'mynameisamanda']

CHECK_THRESHOLD = settings.trygetset('hosting_check_threshold', 60)
OFFLINE_THRESHOLD = settings.trygetset('hosting_offline_threshold', 300)

def setup(bot):
    settings.setdata('%s_is_hosting' % bot.channel.replace('#',''), False)
    settings.setdata('%s_hosted_channel' % bot.channel.replace('#',''), '')

def alert(event):
    if event.channel:
        if event.etype == 'jtvmsg':
            if 'Only the channel owner and channel editors can use the /unhost command.' in event.data:
                print "[Hosting] Not an editor, cannot unhost."
                settings.setdata('%s_auto_unhost' % event.channel, False)

        if event.etype in ['infomsg', 'jtvmsg']: # Should only need jtvmsg
            nowhosting(event) # This needs to be called before the check goes
            # checkifhostonline(event) # This line might need to be outside the if check

        return
        if settings.trygetset('%s_is_hosting' % event.channel, False):
            checkifhostonline(event)


def nowhosting(event):
    if event.data.startswith('HOSTTARGET') and event.data.split()[1] != '-':
        HOSTED_CHANNEL = event.data.split()[1]

        print event.etype, event.channel, event.data

        settings.setdata('%s_is_hosting' % event.channel, True)
        settings.setdata('%s_hosted_channel' % event.channel, event.data.split()[1])

        streamdata = twitchapi.get('streams/%s' % HOSTED_CHANNEL, 'stream')

        print '[Hosting] WE ARE NOW HOSTING %s' % HOSTED_CHANNEL

        if streamdata:
            event.bot.botsay("Now hosting %s, playing %s.  All %s of you, go check it out! %s" %
                (HOSTED_CHANNEL, str(streamdata['game']), event.data.split()[2],'http://twitch.tv/%s' % HOSTED_CHANNEL))
        else:
            print "[Hosting] %s is not streaming." % HOSTED_CHANNEL
    elif event.data.startswith('HOSTTARGET') and event.data.split()[1] == '-':
        print "[Hosting] Unhosting %s " % settings.getdata('%s_hosted_channel' % event.channel)

        settings.setdata('%s_is_hosting' % event.channel, False)
        settings.setdata('%s_hosted_channel' % event.channel, '')


def checkifhostonline(event):
    HOSTED_CHANNEL = settings.getdata('%s_hosted_channel' % event.channel)

    IS_HOSTING = settings.trygetset('%s_is_hosting' % event.channel, True)
    AUTO_UNHOST = settings.trygetset('%s_auto_unhost' % event.channel, True)
    WHITELIST = settings.trygetset('hosting_whitelist', ['monkeys_forever', 'superjoe', 'imayhaveborkedit']) # This should only be temp

    if IS_HOSTING and AUTO_UNHOST and event.channel in WHITELIST:

        LAST_CHECK = settings.trygetset('%s_last_hosting_check' % event.channel, time.time())

        if LAST_CHECK is None:
            settings.setdata('%s_last_hosting_check' % event.channel, time.time())

        elif check_check_threshold(event.channel):
            print '[Hosting] Checking if host is online'
            try:
                streamdata = twitchapi.get('streams/%s' % HOSTED_CHANNEL, 'stream')
            except:
                print "[Hosting] Error grabbing stream data, probably a bad stream."
                event.bot.botsay("%s, I don't think that's a real stream.  If it is, the twitch api is kaput." % event.channel)
            else:
                if streamdata:
                    settings.setdata('%s_last_hosting_check' % event.channel, time.time())

                elif check_offline_threshold(event.channel):
                    print "[Hosting] %s has been offline for long enough, attempting to unhost" % HOSTED_CHANNEL
                    event.bot.botsay('/unhost')


def check_check_threshold(chan):
    return time.time() - settings.getdata('%s_last_hosting_check' % chan, coerceto=float) > CHECK_THRESHOLD

def check_offline_threshold(chan):
    return time.time() - settings.getdata('%s_last_hosting_check' % chan, coerceto=float) > OFFLINE_THRESHOLD

