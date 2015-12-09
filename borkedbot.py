import sys
sys.dont_write_bytecode = True

import chatmanager
import time

from datetime import timedelta
from contextlib import contextmanager
from bs4 import UnicodeDammit
from twisted.internet import reactor, task, protocol
from twisted.words.protocols import irc

try:
    from secrets.auth import TWITCH_IRC_OAUTH_KEY
    assert TWITCH_IRC_OAUTH_KEY
except:
    print 'Please set TWITCH_IRC_OAUTH_KEY in secrets/auth.py'
    sys.exit(1)


class Borkedbot(irc.IRCClient):
    password = TWITCH_IRC_OAUTH_KEY

    mod_linerate = 1
    normal_linerate = 2
    override_linerate = None

    userlist = []
    usertags = {}
    roomtags = {}

    timertask = None
    timertick = 5

    gotops = False
    _max_line_length = None
    _debug_printraw = False

    def __init__(self):
        pass

    @staticmethod
    def reload_manager():
        reload(chatmanager)

    @property
    def lineRate(self):
        if self.override_linerate:
            return override_linerate
        elif self.is_op():
            return self.mod_linerate
        else:
            return self.normal_linerate

    @property
    def nickname(self):
        return self.factory.nickname

    @property
    def channel(self):
        return self.factory.channel

    def is_op(self):
        return self.user_is_op(self.nickname)

    def user_is_op(self, user):
        if user == self.chan():
            return True
        if user in self.usertags:
            data = self.usertags[user].get('user-type', None) # because [mod, global_mod, admin, staff] are all ops
            return data is not '' if data is not None else None

    def user_is_sub(self, user):
        if user == self.chan():
            return True # I don't think this would ever not be the case, but I guess its not if they dont have a sub button
        if user in self.usertags:
            data = self.usertags[user].get('subscriber', None)
            return bool(int(data)) if data else None

    def user_is_turbo(self, user):
        if user in self.usertags:
            data = self.usertags[user].get('turbo', None)
            return bool(int(data)) if data else None

    def timer(self):
        self.send_event(self.chan(), None, 'timer', time.time(), self, None)

    def send_event(self, channel, user, etype, data, bot, isop, extratags=[]):
        del self
        chatmanager.event(**vars())

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

        chatmanager.setup(self)

    def joined(self, channel):
        self.log("Joined %s." % self.chan(channel))
        self.send_event(self.chan(channel), None, 'channeljoin', self.chan(channel), self, None)

        self.timertask = task.LoopingCall(self.timer)
        self.timertask.start(self.timertick, True)

        self.update_mods()

    def receivedMOTD(self, motd):
        print '\n'.join(['\n### MOTD ###', '# ' + '\n# '.join(motd), '############\n'])

    # I'm fairly certain I don't need this any more with the tags enabled
    # def modeChanged(self, user, channel, sett, modes, args):
    #     pass

    def action(self, user, channel, data):
        user = user.split("!")[0]
        self.send_event(self.chan(channel), user, 'action', data, self, self.user_is_op(user))

    def privmsg(self, user, channel, msg):
        fulluser = user
        user = user.split("!")[0]

        if channel != self.factory.channel or user in ['twitchnotify','jtv']:

            if user == 'twitchnotify':
                # print "!!Notification from twitch!! (%s): %s" % (channel, msg)
                self.send_event(self.chan(channel), 'jtv', 'twitchnotify', msg, self, self.user_is_op(user))
                return
        else:
            # def event(channel, user, etype, data, bot, isop):
            self.send_event(self.chan(channel), user, 'msg', msg, self, self.user_is_op(user))


    def noticed(self, user, channel, msg):
        # self.log('Notice from %s in %s: %s' % (user, channel, msg))
        # self.log('Notice: ' + msg)

        if 'The moderators of this room are:' in msg:
            if not self.gotops:
                self.log("Received initial list of ops")
                self.gotops = True

                self.usertags.update({u: {'user-type': 'mod'} for u in msg.split(': ')[1].split(', ')})

        self.send_event(self.chan(), user, 'notice', msg, self, self.user_is_op(user.split('.')[0]))

    def userJoined(self, user, channel):
        pass # requires MEMBERSHIP

    def userLeft(self, user, channel):
        pass # requires MEMBERSHIP


    def irc_CAP(self, prefix, params):
        self.log('CAP %s' % ' '.join(params))

    def irc_CLEARCHAT(self, prefix, params):
        self.log("CLEARCHAT " + ' '.join(params))
        self.send_event(self.chan(), params[1] if len(params) > 1 else None, 'clearchat', self.chan(params[0]), self, self.is_op())

    def irc_HOSTTARGET(self, prefix, params):
        if ' ' in params[1]: params.extend(params.pop().split()) # channel, target, number

        if params[1] == '-': # Exiting host mode
            # No need to log because the notice event will
            self.send_event(self.chan(), None, 'hosting', None, self, self.is_op())
        else:
            self.log('Hosting {} for {} viewers'.format(*params[1:]))
            self.send_event(self.chan(), None, 'hosting', params[1], self, self.is_op(), [params[2]])

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

    def irc_USERSTATE(self, prefix, params):
        self.log('USERSTATE %s' % params)

        # I have confirmed that messages that don't show up don't have userstate sent
        pass

    def irc_GLOBALUSERSTATE(self, prefix, params):
        pass

    def irc_ROOMSTATE(self, prefix, params):
        # self.log('ROOMSTATE %s' % params)
        pass


    def irc_PONG(self, prefix, params):
        pass

    def irc_unknown(self, prefix, command, params, tags=None):
        print 'No handler for irc command "%s": %s (:%s) (%s)' % (command, params, prefix, tags)


    ############################


    def botsay(self, msg, length=None):
        if length == None: length = self._max_line_length

        if isinstance(msg, unicode):
            # I really hope this doesn't break anything
            msg = msg.encode('utf8')

        try:
            self.say(self.factory.channel, msg, length)
        except:
            print '[Borkedbot] How is this not encoded correctly: ', msg

            try:
                self.say(self.factory.channel, UnicodeDammit(msg).unicode_markup.encode('utf8'), length)
            except Exception, e:
                print "Could not force conversion, data may be an object type?"
                msg = str(msg)
                try:
                    self.say(self.factory.channel, msg, length)
                except:
                    print "That didn't work and that's kinda bad: ", e
                    print type(msg), msg

        self.send_event(self.chan(), self.nickname, 'botsay', msg, self, self.is_op())


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

            # print
            # print tagdata
            # print line

            try:
                irccmdtype = line.split(' ')[1]
            except:
                pass

            if irccmdtype == 'PRIVMSG':
                del tagdata['emotes'] # Dont need this (yet?)
                self.usertags.update({line[1:].split('!')[0]: tagdata})

            elif irccmdtype == 'ROOMSTATE':
                self.roomtags.update(tagdata)

            elif irccmdtype == 'USERSTATE':
                self.usertags.update({line.split('#')[1]: tagdata})

            elif irccmdtype == 'GLOBALUSERSTATE':
                pass # NYI

            elif irccmdtype == 'NOTICE':
                pass # {'msg-id': 'something-on/off'}

            else:
                print irccmdtype, tagdata

        # It's either this line or the other commented part and a ton of overridden methods
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