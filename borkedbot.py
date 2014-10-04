import sys
sys.dont_write_bytecode = True

import cPickle, base64, time

from twisted.internet import reactor, task, protocol#, stdio
#from twisted.protocols import basic
from twisted.words.protocols import irc

import chatmanager


class MyBot(irc.IRCClient):
    lineRate = 3

    oplist = []
    userlist = [] # RIP TWITCHCLENT 1
    channelsubs = []

    gotops = False

    timertask = None

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


    def timer(self):
        chatmanager.event(self.channel, None, 'timer', time.time(), self, None)

    def signedOn(self):
        self.join(self.factory.channel)
        print "Signed on as %s.\n" % self.nickname
        self.oplist.append(self.factory.channel.replace('#', ''))
        chatmanager.setup(self)
        chatmanager.event(None, None, 'serverjoin', None, self, None)

        self.sendLine('TWITCHCLIENT 3') # Oh boy here we go

    def joined(self, channel):
        print "Joined %s." % self.chan(channel)
        chatmanager.event(self.chan(channel), None, 'channeljoin', self.chan(channel), self, None)

        self.timertask = task.LoopingCall(self.timer)
        self.timertask.start(30, True)

    def receivedMOTD(self, motd):
        print '\n### MOTD ###'
        print '\n'.join(motd)
        print '############\n'

    def action(self, user, channel, data):
        print "Received action message from %s" % user
        self.privmsg(user, channel, data)

    def modeChanged(self, user, channel, sett, modes, args):
        # user channel           set  modes args
        # jtv  #imayhaveborkedit True o     ('borkedbot',)
        if not self.gotops:
            print "Received initial list of ops"
            self.gotops = True

        #print "Modes changed by %s in %s: %s%s for %s" % (user, channel, '+' if sett else '-', modes, list(args))

        if sett and modes == 'o':
            for u in args:
                self.oplist.append(u)
                chatmanager.event(self.chan(channel), user, 'op', u, self, True)
        elif not sett and modes == 'o':
            for u in args:
                try:
                    self.oplist.remove(u)
                except: pass
                chatmanager.event(self.chan(channel), user, 'deop', u, self, True)

        self.oplist = list(set(self.oplist))

    def privmsg(self, user, channel, msg):
        fulluser = user
        user = user.split("!")[0]
        
        if channel != self.factory.channel:
            if msg.split()[0] in ['EMOTESET', 'USERCOLOR']:
                return
            elif msg.split()[0] == 'SPECIALUSER' and msg.split()[2] == 'subscriber':
                self.channelsubs.append(msg.split()[1])
                self.channelsubs = list(set(self.channelsubs))
                return
            elif msg.split()[0] == 'SPECIALUSER' and msg.split()[2] == 'turbo':
                return

            print "INFO (%s): %s" % (channel, msg)
            chatmanager.event(self.chan(channel), None, 'infomsg', msg, self, user in self.oplist)
            return

        if user == 'jtv':
            if msg.split()[0] in ['EMOTESET', 'USERCOLOR']:
                return
            elif msg.split()[0] == 'SPECIALUSER' and msg.split()[2] == 'subscriber':
                self.channelsubs.append(msg.split()[1])
                self.channelsubs = list(set(self.channelsubs))
                return
            elif msg.split()[0] == 'SPECIALUSER' and msg.split()[2] == 'turbo':
                return


            print "INFO from ttv (%s): %s" % (channel, msg)
            chatmanager.event(self.chan(channel), 'jtv', 'jtvmsg', msg, self, user in self.oplist)
            return

        if user == 'twitchnotify':
            print "!!Notification from twitch!! (%s): %s" % (channel, msg)
            chatmanager.event(self.chan(channel), 'jtv', 'twitchnotify', msg, self, user in self.oplist)
            return

        #       def event(channel, user, etype, data, bot, isop):
        chatmanager.event(self.chan(channel), user, 'msg', msg, self, user in self.oplist)

    def chan(self, c):
        return c.replace('#','')

    def userJoined(self, user, channel):
        self.userlist.append(user)
        self.userlist = list(set(self.userlist))
        chatmanager.event(self.chan(channel), None, 'join', user, self, user in self.oplist)

    def userLeft(self, user, channel):
        try:
            self.userlist.remove(user)
        except:
            print "User not in list to part from (%s)" % user
        self.userlist = list(set(self.userlist))
        chatmanager.event(self.chan(channel), None, 'part', user, self, user in self.oplist)

    def botsay(self, msg):
        self.say(self.factory.channel, msg)

    def quirkyMessage(self, s):
        print "Something odd has happened"
        print s

    def badMessage(self, line, excType, excValue, tb):
        print "Something bad has happened"
        print line, excType, excValue


class MyBotFactory(protocol.ClientFactory):
    protocol = MyBot

    def __init__(self, channel, nickname='borkedbot'):
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
        chan = sys.argv[1]
        mbf = MyBotFactory('#' + chan)

        reactor.connectTCP(server, 6667, mbf)

        reactor.run()

        print "\nTotal run time: %s" % time.time() - starttime
