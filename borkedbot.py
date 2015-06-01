import sys
sys.dont_write_bytecode = True

import chatmanager
import cPickle, base64, time
from datetime import timedelta
from twisted.internet import reactor, task, protocol#, stdio
from twisted.words.protocols import irc
#from twisted.protocols import basic

class Borkedbot(irc.IRCClient):
    lineRate = 2

    opsinchan = set()
    oplist = set()
    extrapos = set()
    gotops = False

    channelsubs = set()
    userlist = []
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
    def ops(self):
        return self.oplist | self.extrapos

    @property
    def usercolors(self):
        return {k:v['USERCOLOR'] for k,v in self.usertags.items()}

    def usercolor(self, user):
        return self.usertags.get(user.lower(), {'USERCOLOR':None}).get('USERCOLOR', None)

    def isop(self, user):
        return user in self.oplist | self.extrapos

    def timer(self):
        self.send_event(self.chan(), None, 'timer', time.time(), self, None)

    def send_event(self, channel, user, etype, data, bot, isop, extratags=[]):
        del self
        chatmanager.event(**vars())

    def reload_manager(self):
        reload(chatmanager)

    def log(self, txt):
        print '[Borkedbot] %s' % txt

    def update_mods(self):
        self.say(self.factory.channel, '/mods')

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

            if user == 'jtv':

                # TODO: remove mod on CLEARCHAT

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

                    elif tag_data in ['admin', 'staff', 'global_mod']:
                        self.opsinchan.add(tag_user)
                        print "Whoop whoop twitch police in the house (%s)" % tag_user
                        self.oplist.add(tag_user)
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


    def botsay(self, msg):
        try:
            self.say(self.factory.channel, str(msg))
        except:
            print '[Borkedbot] Blarg how do I do this shit: %s' % msg

            try:
                self.say(self.factory.channel, msg)
            except Exception, e:
                print 'Ok that didn\'t work, lets try this:'

                try:
                    self.say(self.factory.channel, msg.encode("utf-8"))
                except Exception, e:
                    print 'No that didn\'t work either, wtf how retarded is twisted/unicode'
                    return

        self.send_event(self.chan(), self.nickname, 'botsay', msg, self, self.nickname in self.oplist)


    def ban(self, user, message=None):
        self.botsay('.ban %s' % user)
        if message: self.botsay(message)

    def timeout(self, user, duration=600, message=None):
        self.botsay('.timeout %s %s' % (user, duration))
        if message: self.botsay(message)


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
        self.sendLine('TWITCHCLIENT 3')
        return

        try:
            self.userlist.remove(user)
        except:
            print "User not in list to part from (%s)" % user
        self.userlist = list(set(self.userlist))
        self.send_event(self.chan(channel), None, 'part', user, self, user in self.oplist)

    def quirkyMessage(self, s):
        print "\nSomething odd has happened:"
        print s

    def badMessage(self, line, excType, excValue, tb):
        print "\nSomething bad has happened:"
        print line, excType, excValue

    # def lineReceived(self, line):
        # print line
        # irc.IRCClient.lineReceived(self, line)

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


# def temp_get_channel_chat_server(channel, port80=False):
#     import requests, random
#     r = requests.get('https://api.twitch.tv/api/channels/%s/chat_properties' % channel.replace('#','')).json()
#     servers = r['chat_servers']
#     if port80:
#         return str(random.choice([server for server in servers if server.endswith(':80')]))
#     else:
#         return str(random.choice(servers))


if __name__ == "__main__":
    if len(sys.argv) is not 2:
        print "Usage: python borkedbot.py [twitch_channel]"
    else:
        starttime = time.time()

        server = 'irc.twitch.tv'
        port = 6667
        chan = sys.argv[1] if sys.argv[1].startswith('#') else '#%s' % sys.argv[1]
        mbf = BotFactory(chan, 'borkedbot')

        # server, port = temp_get_channel_chat_server(chan).split(':')

        print 'Connecting to %s on port %s' % (server, port)

        reactor.connectTCP(server, int(port), mbf)
        reactor.suggestThreadPoolSize(20)
        reactor.run()

        print "\nTotal run time: %s (%s)" % (str(timedelta(seconds=int(time.time() - starttime))), time.time() - starttime)

