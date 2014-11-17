import sys
sys.dont_write_bytecode = True

import cPickle, base64, time

from twisted.internet import reactor, task, protocol#, stdio
#from twisted.protocols import basic
from twisted.words.protocols import irc

import chatmanager


class MyBot(irc.IRCClient):
    lineRate = 3

    opsinchan = set()
    oplist = set()
    gotops = False

    channelsubs = set()
    userlist = [] # RIP TWITCHCLENT 1
    usertags = {}

    timertask = None
    timertick = 5

    @property
    def password(self):
        with open('passwd', 'r') as f:
            return base64.b64decode(f.readline())

    @property
    def nickname(self):
        return self.factory.nickname

    @property
    def channel(self):
        return self.factory.channel

    @property
    def usercolors(self):
        return {k:v['USERCOLOR'] for k,v in self.usertags.items()}

    def usercolor(self, user):
        return self.usertags.get(user.lower(), {'USERCOLOR':None}).get('USERCOLOR', None)

    def timer(self):
        self.send_event(self.chan(), None, 'timer', time.time(), self, None)


    def send_event(self, channel, user, etype, data, bot, isop, extratags=[]):
        del self
        chatmanager.event(**vars())

    def log(self, txt):
        print '[Borkedbot] %s' % txt

    def update_mods(self):
        self.botsay('/mods')


    def signedOn(self):
        self.sendLine('TWITCHCLIENT 3') # Oh boy here we go

        self.join(self.factory.channel)
        self.oplist.add(self.chan())
        self.log("Signed on as %s.\n" % self.nickname)

        chatmanager.setup(self)
        self.send_event(None, None, 'serverjoin', None, self, None)


    def joined(self, channel):
        self.log("Joined %s." % self.chan(channel))
        self.send_event(self.chan(channel), None, 'channeljoin', self.chan(channel), self, None)

        self.timertask = task.LoopingCall(self.timer)
        self.timertask.start(self.timertick, True)

        self.update_mods()

    def receivedMOTD(self, motd):
        print '\n'.join(['\n### MOTD ###', '\n'.join(motd), '############\n'])

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
            self.log("WE HAVE A MOD DISCREPANCY HERE:")
            print self.opsinchan - self.oplist
            print
            # self.update_mods()


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

            if user == 'jtv':

                if msg.split()[0] in ['EMOTESET', 'USERCOLOR', 'SPECIALUSER']:
                    tag_user = msg.split()[1]
                    tag_data = msg.split()[2]

                    self.usertags.setdefault(tag_user, dict())

                if msg.split()[0] == 'EMOTESET':
                    self.usertags[tag_user]['EMOTESET'] = tag_data
                    return

                elif msg.split()[0] == 'USERCOLOR':
                    self.usertags[tag_user]['USERCOLOR'] = tag_data
                    return

                elif msg.split()[0] == 'SPECIALUSER':

                    self.usertags[tag_user].setdefault('SPECIALUSER', set())
                    self.usertags[tag_user]['SPECIALUSER'].add(tag_data)

                    if tag_data in ['turbo']:
                        return

                    elif tag_data == 'subscriber':
                        self.channelsubs.add(tag_user)
                        return

                    elif tag_data in ['admin', 'staff']:
                        self.opsinchan.add(tag_user)
                        print "Whoop whoop twitch police in the house (%s)" % tag_user
                        return

                    self.log('Unknown SPECIALUSER: %s' % tag_data)

                elif 'The moderators of this room are:' in msg:
                    self.oplist = set(msg.split(': ')[1].split(', ')) | {self.chan()}
                    if not self.gotops:
                        self.log("Received initial list of ops")
                        self.gotops = True

                self.send_event(self.chan(), 'jtv', 'jtvmsg', msg, self, user in self.oplist)
                return
        else:
            # def event(channel, user, etype, data, bot, isop):
            self.send_event(self.chan(channel), user, 'msg', msg, self, user in self.oplist)

    def chan(self, ch=None):
        c = ch or self.channel
        return c.replace('#','')

    def userJoined(self, user, channel):
        print 'Oh dear we\'re gettings joins.  Resending TC 3'
        self.sendLine('TWITCHCLIENT 3')
        return

        self.userlist.append(user)
        self.userlist = list(set(self.userlist))
        self.send_event(self.chan(channel), None, 'join', user, self, user in self.oplist)

    def userLeft(self, user, channel):
        try:
            self.userlist.remove(user)
        except:
            print "User not in list to part from (%s)" % user
        self.userlist = list(set(self.userlist))
        self.send_event(self.chan(channel), None, 'part', user, self, user in self.oplist)

    def botsay(self, msg):
        self.say(self.factory.channel, msg)
        self.send_event(self.chan(), self.nickname, 'botsay', msg, self, self.nickname in self.oplist)

    def quirkyMessage(self, s):
        print "\nSomething odd has happened:"
        print s

    def badMessage(self, line, excType, excValue, tb):
        print "\nSomething bad has happened:"
        print line, excType, excValue


class MyBotFactory(protocol.ClientFactory):
    protocol = MyBot

    def __init__(self, channel, nickname):
        self.channel = channel
        self.nickname = nickname

    def clientConnectionLost(self, connector, reason):
        print "Lost connection: %s" % reason
        print "Attempting to reconnect..."
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Connection failure: %s" % reason
        print "Could not connect, retrying..."
        connector.connect()


if __name__ == "__main__":
    if len(sys.argv) is not 2:
        print "Usage: python borkedbot.py [channel]"
    else:
        starttime = time.time()

        server = 'irc.twitch.tv'
        chan = sys.argv[1] if sys.argv[1].startswith('#') else '#%s' % sys.argv[1]
        mbf = MyBotFactory(chan, 'borkedbot')

        reactor.connectTCP(server, 6667, mbf)
        reactor.run()

        print "\nTotal run time: %s" % (time.time() - starttime)
