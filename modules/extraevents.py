# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import os, time, json, random, re, requests

from HTMLParser import HTMLParser
import urllib2


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


    # watch?v=n4D-N6aWIV4
    # http://youtube.com/get_video_info?video_id=n4D-N6aWIV4

    if event.etype in ['msg', 'action']:
        if event.channel in ['monkeys_forever']:
            if 'watch?v=' in event.data or 'youtu.be/' in event.data:
                ids = re.findall('watch\?v=(\S{11})', event.data) + re.findall('youtu.be/(.{11})', event.data)

                titles = re.findall('&title=(.*?)&', ''.join([requests.get('http://youtube.com/get_video_info?video_id=%s' % i).text for i in ids]))

                parser = HTMLParser()

                titles = [t.replace('+', ' ') for t in titles]
                titles = [urllib2.unquote(t) for t in titles]
                titles = [parser.unescape(t) for t in titles]

                if len(titles) == 1:
                    event.bot.botsay('Video title for ID %s: %s' % (ids[0], titles[0]))

    # strawpoll.me/api/v2/polls/{id} is json

    # if event.etype == 'action':
        # if event.user == 'hambergo':
            # if 'hugs imayhaveborkedit' in event.data.lower():
                # event.bot.botsay("(▀̿̿Ĺ̯̿̿▀̿ ̿) No touching.")
