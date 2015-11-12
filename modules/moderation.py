# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import re
import time
import requests
import timer
# import supervisor

from secrets import moderation
from twisted.internet import reactor

LOAD_ORDER = 110

def setup(bot):
    pass

def alert(event):
    if event.etype in ['msg', 'action'] and event.bot.user_is_op(event.bot.nickname) and not event.bot.user_is_op(event.user):
        reload(moderation)

        # Spam check
        if check_for_option('spam', event.channel):
            for spam in moderation.SPAM_LIST:
                if spam in event.data.lower().replace(' ',''):
                    # watdo = moderation.SPAM_LIST[spam]
                    watdo = get_moderation_time(spam, moderation.SPAM_LIST, 'fakebans' in moderation.CHANNEL_RULES[event.channel])
                    if watdo:
                        print '[Moderation] Timing %s out for %ss for spam' % (event.user, watdo)
                        timeout(event, watdo)
                        return
                    else:
                        print '[Moderation] Banning %s for spam' % event.user
                        ban(event)
                        return

        # Copypasta check
        if check_for_option('pasta', event.channel):
            for pasta in moderation.COPYPASTAS:
                if pasta in event.data.lower().replace(' ',''):
                    # watdo = moderation.COPYPASTAS[pasta]
                    watdo = get_moderation_time(pasta, moderation.COPYPASTAS, 'fakebans' in moderation.CHANNEL_RULES[event.channel])
                    if watdo:
                        print '[Moderation] Timing %s out for %ss for copypasta' % (event.user, watdo)
                        timeout(event, watdo)
                        break
                    else:
                        print '[Moderation] Banning %s for copypasta' % event.user
                        ban(event)
                        break

        # Long message check
        if check_for_option('longmsg', event.channel):
            if len(event.data) > moderation.LONG_MESSAGE_LENGTH:
                print '[Moderation] Clearing long message from %s' % event.user
                timeout(event, 10, "That's way too much text for chat dude.")

        # Banned names check
        if check_for_option('names', event.channel):
            for pat in moderation.NAMES_BLACKLIST:
                if re.match(pat, event.user):
                    print '[Moderation] Banning %s for name' % event.user
                    ban(event)

    if event.etype in ['msg', 'action'] and not event.isop:
        inspect_for_bad_link(event)


def check_for_option(option, channel):
    if channel in moderation.CHANNEL_RULES:
        if option in moderation.CHANNEL_RULES[channel] or 'all' in moderation.CHANNEL_RULES[channel]:
            if '!' + option not in moderation.CHANNEL_RULES[channel]:
                return True
    return False

def get_moderation_time(spam, table, fakebans=False):
    watdo = table[spam]
    return watdo if not fakebans else moderation.MAX_TIMEOUT_DURATION


def ban(event, message=None, fakeban=False):
    with event.bot.unlock_ratelimit(): # I have no idea if this works with the deferreds
        if message:
            event.bot.botsay(message)

        _delayed_timeout(event.bot, 0.4, event.user, 600)

        if fakeban:
            _delayed_timeout(event.bot, 0.9, event.user, moderation.MAX_TIMEOUT_DURATION)
        else:
            _delayed_ban(event.bot, 0.9, event.user)

        time.sleep(1)


def timeout(event, duration=600, message=None):
    with event.bot.unlock_ratelimit():
        if message:
            event.bot.botsay(message)
        _delayed_timeout(event.bot, 0.4, event.user, duration)
        _delayed_timeout(event.bot, 0.9, event.user, duration)

        time.sleep(1)


def _delayed_ban(bot, delay, user):
    reactor.callLater(delay, bot.ban, user)

def _delayed_timeout(bot, delay, user, duration):
    reactor.callLater(delay, bot.timeout, user, duration)


def expand_googl(url):
    r = requests.get('https://www.googleapis.com/urlshortener/v1/url?shortUrl=' + url)
    try:
        if r.json()['status'] == 'OK':
            return r.json()['longUrl']
        elif r.json()['status'] in ['REMOVED', 'MALWARE']:
            return
        else:
            print "wtf is this: %s" % r.json()
    except:
        print r.status_code, r.reason
        print r.text

        # FIX MAKE BETTER

def expand_shortlink(url):
    r = requests.head(url)
    if r.status_code == 301:
        return r.headers['location']
    elif r.status_code == 404:
        return False
    else:
        print 'Unknown thing:', r, r.reason


def inspect_for_bad_link(event):
    t0 = time.time()
    foundlinks = [m[0] for m in moderation.LINK_REGEX.findall(event.data) if m]
    foundlinks = list(set(foundlinks))

    if foundlinks:
        print '[Moderation-Scan] Found: %s in %.4fms' % (str(foundlinks), (time.time() - t0)*1000)
        for l in foundlinks:
            if not (l.startswith('http://') or l.startswith('https://')): l = 'http://' + l

            if any([wll in l for wll in moderation.INSPECT_WHITELIST]): # should change to regex matching + change whitelist to regex format
                print '[Moderation-Scan] Link is whitelisted'
                continue

            tim = timer.Timer('link scanner', True)
            badlink = scan_link(l)

            tim.stop()
            print '[Moderation-Scan] Link scanned in %.4f ms' % (tim.runtime() * 1000)

            if badlink:
                print '[Moderation-Scan] Bad link detected (%s)' % badlink

                if check_for_option('inspect', event.channel):

                    if check_for_option('inspect-warning', event.channel):
                        bl_warning = 'That looks like a bad link, don\'t touch it. (%s)' % badlink
                    else:
                        bl_warning = None

                    ban(event, bl_warning)

                if check_for_option('inspect-warning', event.channel):
                    event.bot.botsay('I would advise against clicking that link. (%s)' % badlink)

                if check_for_option('inspect-propagate', event.channel):
                    pass

                break


def scan_link(link):
    try:
        r = requests.head(link, timeout=7, headers={'User-agent': moderation.USER_AGENT})

    except requests.exceptions.ConnectionError as e:
        if e.args[0][1].args[1] in ['getaddrinfo failed', 'Name or service not known']:
            print "Alright that's not a real link"
            # This is not a real link
            return

    except Exception as e:
        print 'Something fucked up checking %s:' % link
        print e
        return

    if r.status_code is not 200:
        print '[Moderation-Scan] Non 200 response:', r.status_code, r.reason
        print r.headers

    if r.status_code == 404:
        return

    if r.is_redirect:
        try:
            with requests.Session() as s:
                s.max_redirects = 10
                r2 = s.head(link, allow_redirects=True, timeout=7, headers={'User-agent': moderation.USER_AGENT})
        except requests.exceptions.TooManyRedirects as e:
            print 'Who honestly uses more than 10 redirects for something, really now.'
            return

        loc = r.headers.get('location')

        print '[Moderation-Scan] Redirect destination status:', r2.status_code, r2.reason
        print '[Moderation-Scan] Redirect history:', [x.url for x in r2.history]
        if r2.url != r2.history[-1].url:
            print '[Moderation-Scan] Destination:', r2.url
            loc = r2.url
        print r2.headers

        for sl in moderation.SPAM_LIST:
            if sl in loc:
                return 'Redirect to spam'

        # 'content-disposition': 'attachment; filename="Screenshot###.scr"
        if r2.headers.get('content-disposition', '').startswith('attachment;'):
            if re.search('filename\=.+?\.scr', r2.headers.get('content-disposition'), re.IGNORECASE):
                return '.scr download'
        elif re.search(moderation.SPECIAL_REGEX['dropbox_scr'], loc):
            return '.scr download'

        if loc.endswith('.scr') and r2.headers.get('content-type', '').startswith('application'):
            return '.scr download'

        if r2.headers.get('transfer-encoding') == 'chunked':
            print '[Moderation-Scan] Most likely a download, but I have no good solution for this.' 
            # perhaps this should only return if it went through a link shortener
            # return 'Redirect to download'

    elif r.headers.get('content-type', '').startswith('text'): # preferably text/html but I don't know if that's always set
        #TODO: various if checks to make sure what we're about to do is sane

        print '[Moderation-Scan] Inspecting page source'

        ## Meta redirect check
        rget = requests.get(link, timeout=7, headers={'User-agent': moderation.USER_AGENT})

        # This should work and I don't know if I want to bring in BeautifulSoup just for this
        metamatch = re.search(moderation.SPECIAL_REGEX['meta'], rget.text)

        if metamatch:
            print '[Moderation-Scan] Scanning meta redirect to "%s"' % metamatch.groups()[0]
            return scan_link(metamatch.groups()[0])
            # I hope I don't have an infinite redirect issue, that'd be awkward.
            # All i'd need to do is add a recursion level arg to scan_link() and stop after X recursions

        # this one seems to use a timed js redirect, i might just blacklist this link in the future
        if 'xaa.su' in rget.url.lower():
            match_xaasu = re.search(moderation.SPECIAL_REGEX['xaa.su'], rget.text)
            if match_xaasu:
                print '[Moderation-Scan] xaa.su redirect found: %s' % match_xaasu.groups()[0]
                return scan_link(str(match_xaasu.groups()[0]))

        # Other checks
        # check for links to exes and scrs and warn, maybe return a (ban_duration:int [-1 no ban, 0 ban, 1+ timeout duration], reason:str)
    elif 'content-type' in r.headers:
        print '[Moderation-Scan] Non text destination: %s' % r.headers.get('content-type')
        print r.headers

    else:
        print '[Moderation-Scan] No content-type sent'
        print r.headers
