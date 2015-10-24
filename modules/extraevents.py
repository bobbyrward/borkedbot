# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import re
import requests
import urllib2

from HTMLParser import HTMLParser


LOAD_ORDER = 30


def setup(bot):
    pass


def alert(event):
    # Sub alert
    if event.etype == 'twitchnotify':
        if event.channel in ['monkeys_forever', 'superjoe', 'kizzmett', 'moodota2', 'unsanitylive']:
            msg = 'ヽ༼ຈل͜ຈ༽ﾉ RE-SUB HYPE! PRAISE %s' % event.data.split()[0].upper()
            if 'just subscribed!' in event.data:
                extra = ''
                if event.channel in ['monkeys_forever', 'kizzmett']:
                    # extra = ' | If you want an invite to the sub guild use !guildinvite (Make sure you have \"Allow guild invites from -> Anyone\" enabled)'
                    extra = ''
                event.bot.botsay(msg + extra)

            if 'subscribed for ' in event.data:
                event.bot.botsay(msg)

    #######################################
    ## TODO:

    # Move this code over to some infoposter.py module
    # It would post titles to youtube links, twitter post text
    # steam game link info, more as I think of them

    # watch?v=n4D-N6aWIV4
    # http://youtube.com/get_video_info?video_id=n4D-N6aWIV4

    if event.etype in ['msg', 'action']:
        if event.channel in ['monkeys_forever', 
                             'unsanitylive', 
                             'pelmaleon', 
                             'mynameisamanda', 
                             'imayhaveborkedit', 
                             'barnyyy', 
                             'moodota2', 
                             'gixgaming', 
                             'kazkarontwo', 
                             'lamperkat', 
                             'f4ldota', 
                             'kizzmett']:
            if ('youtube.com/watch?' in event.data or 'youtu.be/' in event.data) and not event.data.strip().startswith('!'):# and event.user != 'rime_':
                print '[ExtraEvents] Found youtube link, looking up title'

                ids = re.findall('watch\?.*?v=(\S{11})', event.data) + re.findall('youtu.be/(.{11})', event.data)
                ids = list(set(ids))
                print '[ExtraEvents] Found ids: %s' % ids

                ytdata = {}

                for i in ids:
                    ytdata[i] = get_youtube_title(i)
                    print '[ExtraEvents] Found title for %s: %s' % (i, ytdata[i])

                for ytid in ytdata:
                    if ytid:
                        event.bot.botsay('Video title for ID %s: %s' % (ytid, ytdata[ytid]))


    # strawpoll.me/api/v2/polls/{id} is json

    # if event.etype == 'action':
        # if event.user == 'hambergo':
            # if 'hugs imayhaveborkedit' in event.data.lower():
                # event.bot.botsay("(▀̿̿Ĺ̯̿̿▀̿ ̿) No touching.")


def get_youtube_title(v_id, backup=False):
    if not backup:
        try:
            title = re.findall('&title=(.*?)&', requests.get('http://youtube.com/get_video_info?video_id=%s' % v_id).content)[0]
            title = title.replace('+', ' ')
        except:
            print '[ExtraEvents] Youtube lookup failed, using backup method'
            return get_youtube_title(v_id, True)

    else:
        ytd = requests.get('https://www.youtube.com/watch?v=%s' % v_id).content
        title = ytd[ytd.index('<title>')+7:ytd.index('</title>')-10]

    parser = HTMLParser()

    title = urllib2.unquote(title)
    title = parser.unescape(title)

    return title


def get_strawpoll(sid):
    strawapi = 'http://strawpoll.me/api/v2/polls/%s'
    data = requests.get(requests.get(strawapi % sid))

    '''

    {u'multi': False,
     u'options': [
      u'Hotline Miami 2 - The coolest drug trip ever',
      u'Please, Don\u2019t Touch Anything - Where I will undoubtedly touch something',
      u'The Long Dark - New map and content? Say whaaaat?',
      u'Dead Rising 1 - For the fabillionth time',
      u'GTA 5 - The hunt for every quest I can find'
     ],
     u'permissive': False,
     u'title': u"Hey, whats a game you'd like to see on cast. Pick a good one.",
     u'votes': [47, 85, 29, 64, 85]}

    '''