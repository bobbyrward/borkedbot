# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import re, time, requests
from secrets import moderation
from twisted.internet import reactor

LOAD_ORDER = 110


def setup(bot):
    reload(moderation)

def alert(event):
    if event.etype in ['msg', 'action'] and 'borkedbot' in event.bot.oplist and event.user not in event.bot.oplist:

        # Spam check
        if check_for_option('spam', event.channel):
            for spam in moderation.SPAM_LIST:
                if spam in event.data.lower().replace(' ',''):
                    # watdo = moderation.SPAM_LIST[spam]
                    watdo = get_moderation_time(spam, moderation.SPAM_LIST, 'fakebans' in moderation.CHANNEL_RULES[event.channel])
                    if watdo:
                        print '[Moderation] Timing %s out for %ss for spam' % (event.user, watdo)
                        timeout(event, watdo, 'Spam is bad and you should feel bad.')
                        return
                    else:
                        print '[Moderation] Banning %s for spam' % event.user
                        ban(event, 'Spam is bad and you should feel bad.')
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
            if len(event.data) > moderation.LONG_MESSAGE_LENGTH and event.user not in event.bot.oplist:
                print '[Moderation] Clearing long message from %s' % event.user
                timeout(event, 10, "That's way too much text for chat dude.")

        # Banned names check
        if check_for_option('names', event.channel):
            for pat in moderation.NAMES_BLACKLIST:
                if re.match(pat, event.user):
                    print '[Moderation] Banning %s for name' % event.user
                    ban(event)

# Fuck it we're doing it go away code
#        # Shortlinks check
#        if check_for_option('shortlinks', event.channel):
#            if 'goo.gl/' in event.data.lower():
#                links = re.findall('goo.gl/......', event.data, re.I)
#                links = list(set(links))
#                print '[Moderation] Found goo.gl link, looking up %s' % links
#
#                for l in links:
#                    goog = expand_shortlink('http://' + l)
#                    print '[Moderation] Resolved %s -> %s' % (l, goog)
#
#                    for sl in moderation.SPAM_LIST.keys():
#                        if sl in goog:
#                            # watdo = shortlinks[sl]
#                            watdo = get_moderation_time(sl, moderation.SPAM_LIST, 'fakebans' in moderation.CHANNEL_RULES[event.channel])
#
#                            if watdo:
#                                print '[Moderation] Timing out %s for %ss for shortlink' % (event.user, watdo)
#                                timeout(event, watdo)
#                            else:
#                                print '[Moderation] Banning %s for shortlink' % event.user
#                                ban(event)
#
#                            return
#                    else:
#                        print '[Moderation] Found a new shortlink, do something: %s -> %s' % (l, goog)
#                        timeout(event, 1, "I don't know if that's a bad link or not.  It's probably bad though.")
#                        # break
#
#            elif 'bit.ly/' in event.data.lower():
#                links = re.findall('bit.ly/\S*', event.data, re.I)
#                links = list(set(links))
#                print '[Moderation] Found bit.ly link, looking up %s' % links
#
#                for l in links:
#                    bitly = expand_shortlink('http://' + l)
#                    print '[Moderation] Resolved %s -> %s' % (l, bitly)
#
#                    for sl in moderation.SPAM_LIST.keys():
#                        if sl in bitly:
#                            # watdo = shortlinks[sl]
#                            watdo = get_moderation_time(sl, moderation.SPAM_LIST, 'fakebans' in moderation.CHANNEL_RULES[event.channel])
#
#                            if watdo:
#                                print '[Moderation] Timing out %s for %ss for shortlink' % (event.user, watdo)
#                                timeout(event, watdo)
#                            else:
#                                print '[Moderation] Banning %s for shortlink' % event.user
#                                ban(event)
#
#                            return
#                    else:
#                        print '[Moderation] Found a new shortlink, do something: %s -> %s' % (l, bitly)
#                        timeout(event, 1, "I don't know if that's a bad link or not.  It's probably bad though.  If it's fine a mod can post it again.")
#                        # break

    if event.etype in ['msg', 'action'] and not event.isop:
        inspect_for_bad_link(event)

def check_for_option(option, channel):
    return channel in moderation.CHANNEL_RULES and (option in moderation.CHANNEL_RULES[channel] or 'all' in moderation.CHANNEL_RULES[channel]) and 'none' not in moderation.CHANNEL_RULES[channel]

def get_moderation_time(spam, table, fakebans=False):
    watdo = table[spam]
    return watdo if not fakebans else moderation.MAX_TIMEOUT_DURATION

def ban(event, message=None, fakeban=False):
    _delayed_timeout(event.bot, 0.1, event.user, 600)
    _delayed_timeout(event.bot, 0.4, event.user, 600)

    if fakeban:
        _delayed_timeout(event.bot, 0.8, event.user, moderation.MAX_TIMEOUT_DURATION)
    else:
        _delayed_ban(event.bot, 0.8, event.user)

def timeout(event, duration=600, message=None):
    _delayed_timeout(event.bot, 0.1, event.user, duration)
    _delayed_timeout(event.bot, 0.4, event.user, duration)
    _delayed_timeout(event.bot, 0.8, event.user, duration)

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
        print '[Moderation-Scan] Found: %s in %4.4fms' % (str(foundlinks), (time.time() - t0)*1000)
        for l in foundlinks:
            if not (l.startswith('http://') or l.startswith('https://')): l = 'http://' + l

            if any([wll in l for wll in moderation.INSPECT_WHITELIST]): # should change to regex matching + change whitelist to regex format
                print '[Moderation-Scan] Link is whitelisted'
                continue

            badlink = scan_link(l)
            if badlink:
                print '[Moderation-Scan] Bad link detected'
                if check_for_option('inspect', event.channel):
                    ban(event, 'That looks like a bad link, don\'t touch it. (%s)' % badlink)
                # else:
                    # event.bot.botsay('I would advise against clicking that link. (%s)' % badlink)
                break


def scan_link(link):
    try:
        r = requests.head(link, headers={'User-agent': moderation.USER_AGENT})
    except Exception as e:
        if isinstance(e, requests.exceptions.ConnectionError):
            if e.args[0][1].args[1] in ['getaddrinfo failed', 'Name or service not known']:
                # This is not a real link
                return
        print 'Something fucked up checking %s:' % link
        print e
        return

    if r.status_code is not 200:
        print '[Moderation-Scan] Non 200 response:'
        print r.status_code, r.reason
        print r.headers

    if r.status_code == 404:
        return

    if r.is_redirect:
        r2 = requests.head(link, allow_redirects=True)
        print r2.status_code, r2.reason
        print [x.url for x in r2.history]
        print r2.headers

        if r2.headers.get('transfer-encoding') == 'chunked':
            # print 'this may be a download'
            return 'Redirect to download'

        # 'content-disposition': 'attachment; filename="Screenshot093.scr"
        if r2.headers.get('content-disposition', '').startswith('attachment;'):
            if re.search('filename\=.+?\.scr', r2.headers.get('content-disposition'), re.IGNORECASE):
                return '.scr download'

        loc = r.headers.get('location')
        # for l in SCAN_BLACKLIST:
            # if l in loc:
                # return 'Redirect to link shortener'

        for sl in moderation.SPAM_LIST:
            if sl in loc:
                return 'Redirect to spam'

        print '[Moderation-Scan] Found redirect: %s' % loc

    else:
        # various if checks to make sure what we're about to do is sane

        print '[Moderation-Scan] Inspecting page source'

        ## Meta redirect check
        rget = requests.get(link, headers={'User-agent': moderation.USER_AGENT})

        # This should work and I don't know if I want to bring in BeautifulSoup just for this
        metamatch = re.search(r'\<meta.+?url\=(.+?)">', rget.text, re.IGNORECASE)

        if metamatch:
            print '[Moderation-Scan] Scanning meta redirect to "%s"' % metamatch.groups()[0]
            return scan_link(metamatch.groups()[0])
            # I hope I don't have an infinite redirect issue, that'd be awkward.
            # All i'd need to do is add a recursion level arg to scan_link() and stop after X recursions


        # Other checks
        # check for links to exes and scrs and warn, maybe return a (ban_duration:int [-1 no ban, 0 ban, 1+ timeout duration], reason:str)
