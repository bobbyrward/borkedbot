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
        if event.channel in ['monkeys_forever', 'superjoe', 'kizzmett', 'unsanitylive']:
            if 'just subscribed!' in event.data:
                extra = ''
                if event.channel in ['monkeys_forever', 'kizzmett']:
                    extra = ' | If you want an invite to the sub guild use !guildinvite'

                event.bot.botsay('ヽ༼ຈل͜ຈ༽ﾉ SUB HYPE! PRAISE %s%s' % (event.data.split()[0].upper(), extra))

            if 'subscribed for ' in event.data:
                event.bot.botsay('ヽ༼ຈل͜ຈ༽ﾉ RE-SUB HYPE! PRAISE %s' % event.data.split()[0].upper())


    # watch?v=n4D-N6aWIV4
    # http://youtube.com/get_video_info?video_id=n4D-N6aWIV4

    if event.etype in ['msg', 'action']:
        if event.channel in ['monkeys_forever', 'unsanitylive', 'pelmaleon', 'mynameisamanda', 'imayhaveborkedit', 'barnyyy']:
            if 'watch?v=' in event.data or 'youtu.be/' in event.data:
                print '[ExtraEvents] Found youtube link, looking up title'

                ids = re.findall('watch\?v=(\S{11})', event.data) + re.findall('youtu.be/(.{11})', event.data)
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


def get_youtube_title(v_id):
    try:
        title = re.findall('&title=(.*?)&', requests.get('http://youtube.com/get_video_info?video_id=%s' % v_id).text)[0]
    except:
        print '[ExtraEvents] Youtube lookup failed, using backup method'
        title = None

    if not title:
        ytd = requests.get('https://www.youtube.com/watch?v=%s' % v_id).text
        title = ytd[ytd.index('<title>')+7:ytd.index('</title>')-10]
    else:
        title = title.replace('+', ' ')

    parser = HTMLParser()

    title = urllib2.unquote(title)
    title = parser.unescape(title)

    return title
