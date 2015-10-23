import sys
sys.dont_write_bytecode = True

import chatmanager
import time

from datetime import timedelta
from contextlib import contextmanager
from twisted.internet import reactor, task, protocol
from twisted.words.protocols import irc

try:
    from secrets.auth import TWITCH_IRC_OAUTH_KEY
    assert TWITCH_IRC_OAUTH_KEY
except:
    print 'Please set TWITCH_IRC_OAUTH_KEY in secrets/auth.py'
    sys.exit(1)


class Borkedbot(irc.IRCClient):
    lineRate = 2
    password = TWITCH_IRC_OAUTH_KEY

    opsinchan = set()
    oplist = set()
    extrapos = set()
    gotops = False

    channelsubs = set()
    userlist = []
    usertags = {}
    roomtags = {}

    timertask = None
    timertick = 5

    _max_line_length = None
    _debug_printraw = False

    def __init__(self):
        pass

    @property
    def nickname(self):
        return self.factory.nickname

    @property
    def channel(self):
        return self.factory.channel

    @property
    def ops(self):
        return self.oplist | self.extrapos

    @property
    def usercolors(self):
        return {k: v['USERCOLOR'] for k, v in self.usertags.items()}

    def usercolor(self, user):
        return self.usertags.get(user.lower(), {'USERCOLOR':None}).get('USERCOLOR', None)

    def isop(self, user):
        return user in self.oplist | self.extrapos

    def timer(self):
        self.send_event(self.chan(), None, 'timer', time.time(), self, None)

    def send_event(self, channel, user, etype, data, bot, isop, extratags=[]):
        del self
        chatmanager.event(**vars())

    @staticmethod
    def reload_manager(self):
        reload(chatmanager)

    def log(self, txt):
        print '[Borkedbot] %s' % txt

    def update_mods(self):
        self.say(self.factory.channel, '/mods')

    @contextmanager
    def unlock_ratelimit(self):
        lr = self.lineRate
        self.lineRate = 0
        yield
        self.lineRate = lr

    @contextmanager
    def unlock_linelength(self, length=1000):
        oml = self._max_line_length
        self._max_line_length = length
        yield
        self._max_line_length = oml

    def signedOn(self):
        self.send_event(None, None, 'serverjoin', None, self, None)

        self.sendLine('CAP REQ :twitch.tv/commands')
        self.sendLine('CAP REQ :twitch.tv/tags')

        self.log("Signed on as %s.\n" % self.nickname)
        self.join(self.factory.channel)
        self.oplist.add(self.chan())

        chatmanager.setup(self)

    def joined(self, channel):
        self.log("Joined %s." % self.chan(channel))
        self.send_event(self.chan(channel), None, 'channeljoin', self.chan(channel), self, None)

        self.timertask = task.LoopingCall(self.timer)
        self.timertask.start(self.timertick, True)

        self.update_mods()

    def receivedMOTD(self, motd):
        print '\n'.join(['\n### MOTD ###', '# '.join(motd), '############\n'])

    def modeChanged(self, user, channel, sett, modes, args):
        # user channel           set  modes args
        # jtv  #imayhaveborkedit True o     ('borkedbot',)

        #print "Modes changed by %s in %s: %s%s for %s" % (user, channel, '+' if sett else '-', modes, list(args))

        if sett and modes == 'o':
            for u in args:
                self.opsinchan.add(u)
                self.send_event(self.chan(channel), user, 'op', u, self, True)

        elif not sett and modes == 'o':
            for u in args:
                self.opsinchan.discard(u)
                self.send_event(self.chan(channel), user, 'deop', u, self, True)

        if self.opsinchan - self.oplist and self.gotops:
            # This might be only for new mods now, need to check
            self.log("WE HAVE A MOD DISCREPANCY: %s" % list(self.opsinchan - self.oplist))
            self.extrapos = self.extrapos | (self.opsinchan - self.oplist)
            self.update_mods()

    def action(self, user, channel, data):
        user = user.split("!")[0]
        self.send_event(self.chan(channel), user, 'action', data, self, user in self.oplist)

    def privmsg(self, user, channel, msg):
        fulluser = user
        user = user.split("!")[0]

        if channel != self.factory.channel or user in ['twitchnotify','jtv']:

            if user == 'twitchnotify':
                # print "!!Notification from twitch!! (%s): %s" % (channel, msg)
                self.send_event(self.chan(channel), 'jtv', 'twitchnotify', msg, self, user in self.oplist)
                return
        else:
            # def event(channel, user, etype, data, bot, isop):
            self.send_event(self.chan(channel), user, 'msg', msg, self, user in self.oplist)


    def noticed(self, user, channel, msg):
        # self.log('Notice from %s in %s: %s' % (user, channel, msg))
        # self.log('Notice: ' + msg)

        if 'The moderators of this room are:' in msg:
            self.oplist = set(msg.split(': ')[1].split(', ')) | {self.chan()}
            if not self.gotops:
                self.log("Received initial list of ops")
                self.gotops = True

        self.send_event(self.chan(), user, 'notice', msg, self, user.split('.')[0] in self.oplist)


    def irc_CAP(self, prefix, params):
        self.log('CAP %s' % ' '.join(params))

    def irc_CLEARCHAT(self, prefix, params):
        self.log("CLEARCHAT " + ' '.join(params))
        self.send_event(self.chan(), params[1] if len(params) > 1 else None, 'clearchat', self.chan(params[0]), self, self.nickname in self.oplist)

    def irc_HOSTTARGET(self, prefix, params):
        if ' ' in params[1]: params.extend(params.pop().split()) # channel, target, number

        if params[1] == '-': # Exiting host mode
            # No need to log because the notice event will
            self.send_event(self.chan(), None, 'hosting', None, self, self.nickname in self.oplist)
        else:
            self.log('Hosting {} for {} viewers'.format(*params[1:]))
            self.send_event(self.chan(), None, 'hosting', params[1], self, self.nickname in self.oplist, [params[2]])

    def irc_RECONNECT(self, prefix, params):
        self.log('Twitch chat sever restarting in 30 seconds, disconnect imminent.')
        self.log('Estimated restart at %s' % str(time.time() + 30.0))
        self.botsay('Twitch chat server restart in 30 seconds.  Bot will reconnect shortly.')

    def irc_RPL_NAMREPLY(self, prefix, params):
        return
        #self.log('Receiving names: ' + ' '.join(params))

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        return
        #self.log('Names list received.')


    ### I need tags for these

    def irc_USERSTATE(self, prefix, params):
        self.log('USERSTATE %s' % params)

        # I have confirmed that messages that don't show up don't have userstate sent
        pass

    def irc_GLOBALUSERSTATE(self, prefix, params):
        pass

    def irc_ROOMSTATE(self, prefix, params):
        # self.log('ROOMSTATE %s' % params)
        pass

    ########################

    def irc_PONG(self, prefix, params):
        pass

    def irc_unknown(self, prefix, command, params, tags=None):
        print 'No handler for irc command "%s": %s (:%s) (%s)' % (command, params, prefix, tags)





    ############################

    def botsay(self, msg, length=None):
        if length == None: length = self._max_line_length
        try:
            self.say(self.factory.channel, msg, length)
        except:
            print '[Borkedbot] Blarg how do I do this shit: %s' % msg

            try:
                self.say(self.factory.channel, msg.decode("utf-8"), length)
            except Exception, e:
                print 'No that didn\'t work either, wtf how retarded is twisted/unicode'

                try:
                    self.say(self.factory.channel, msg.encode("utf-8"), length)
                except Exception, e:
                    print 'I give up'
                    return

        self.send_event(self.chan(), self.nickname, 'botsay', msg, self, self.nickname in self.oplist)


    def ban(self, user, message=None):
        self.botsay('.ban %s' % user)
        if message:
            self.botsay(message)

    def timeout(self, user, duration=600, message=None):
        self.botsay('.timeout %s %s' % (user, duration))
        if message:
            self.botsay(message)



    def chan(self, ch=None):
        c = ch or self.channel
        return c.replace('#','')

    # def userJoined(self, user, channel):
        # return
        # self.userlist.append(user)
        # self.userlist = list(set(self.userlist))
        # self.send_event(self.chan(channel), None, 'join', user, self, user in self.oplist)

    # def userLeft(self, user, channel):
        # return
        # try:
            # self.userlist.remove(user)
        # except:
            # print "User not in list to part from (%s)" % user
        # self.userlist = list(set(self.userlist))
        # self.send_event(self.chan(channel), None, 'part', user, self, user in self.oplist)

    def quirkyMessage(self, s):
        print "\nSomething odd has happened:"
        print s
        print

    def lineReceived(self, line):
        if self._debug_printraw:
            print line

        if line.startswith('@'):
            v3line = line

            tags, line = v3line.split(' :', 1)
            line = ':' + line

            tagdata = {t.split('=')[0]:t.split('=')[1] for t in tags[1:].split(';')}
            print
            print tagdata
            print line
        else:
            tagdata = None


        if tagdata:
            # check to see which kind of tags are sent buy looking for a specific trag
            if 'user-type' in tagdata:
                if not 'emote-sets' in tagdata:
                    del tagdata['emotes'] # Dont need this (yet?)

                self.usertags.update({line[1:].split('!')[0]: tagdata})

            if 'msg-id' in tagdata:
                pass # room state changes but with no data

            if 'slow' in tagdata:
                self.roomtags['slow'] = tagdata['slow'] # I can change these to dict.update if 'slow' is ONLY sent with these types of messages

            if 'r9k' in tagdata:
                self.roomtags['r9k'] = tagdata['r9k']
                pass # set roomtags for slow, subs-only, broadcaster-lang, r9k (not sure if all are always sent)

            if 'subs-only' in tagdata:
                self.roomtags['subs-only'] = tagdata['subs-only']

            if 'broadcaster-lang' in tagdata:
                self.roomtags['broadcaster-lang'] = tagdata['broadcaster-lang']

            # The if stack is probably not the best way to deal with this but oh well
            # maybe regex the irc command type and update tags from that
            # orrrrr line.split(' ')[1]


        # It's either this line or the other commented part
        irc.IRCClient.lineReceived(self, line)

'''
        line = irc.lowDequote(line)
        try:
            prefix, command, params = irc.parsemsg(line)
            if command in irc.numeric_to_symbolic:
                command = irc.numeric_to_symbolic[command]
            self._handleCommand(command, prefix, params, tags=tagdata)
        except irc.IRCBadMessage:
            irc.IRCClient.badMessage(self, v3line, *sys.exc_info())

    def _handleCommand(self, command, prefix, params, tags=None):
        method = None

        if tags:
            if (command.startswith('RPL') or command.startswith('ERR')):
                print 'uh i dunno what to do here because it has tags I guess I just ignore them'
                irc.IRCClient.handleCommand(self, command, prefix, params)
                return
            else:
                method = getattr(self, "irc_%s" % command, None)
        else:
            irc.IRCClient.handleCommand(self, command, prefix, params)
            return

        try:
            if method is not None:
                method(prefix, params)
            else:
                self.irc_unknown(prefix, command, params)
        except:
            irc.log.deferr()
'''


class BotFactory(protocol.ClientFactory):
    protocol = Borkedbot

    def __init__(self, channel, nickname):
        self.channel = channel
        self.nickname = nickname

    def clientConnectionLost(self, connector, reason):
        print "Lost connection at %s: %s" % (time.time(), reason)
        print "Attempting to reconnect..."
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Connection failure at %s: %s" % (time.time(), reason)
        print "Could not connect, retrying..."
        connector.connect()

if __name__ == "__main__":
    if len(sys.argv) is not 2:
        print "Usage: python borkedbot.py [twitch_channel]"
    else:
        starttime = time.time()

        server = 'irc.twitch.tv'
        port = 6667
        chan = '#{}'.format(sys.argv[1])
        mbf = BotFactory(chan, 'borkedbot')

        print 'Connecting to %s on port %s' % (server, port)

        reactor.connectTCP(server, int(port), mbf)
        reactor.suggestThreadPoolSize(20)
        reactor.run()

        print "\nTotal run time: %s (%s)" % (str(timedelta(seconds=int(time.time() - starttime))), time.time() - starttime)

    # TODO: Add way to remake and reconnect the bot