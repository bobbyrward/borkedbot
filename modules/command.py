# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import time
import subprocess
import random

DISABLE_MODULE = True
LOAD_ORDER = 70


class OK(): pass                    # Everything is ok
class DELAY_LOCKED(): pass          # Not enough time has passed to use this command again
class WRONG_TRIGGER():  pass        # Just represents that this isn't the command you're looking for
class BAD_CHANNEL(): pass           # Can't use this command in this channel for some reason (black/white list)
class BAD_MESSAGE(): pass           # The message is empty or otherwise unusable
class OP_RESTRICTED(): pass         # Only ops can use these (Might not be used due to implementation)
class HOST_RESTRICTED(): pass       # Only the broadcaster can use these
class SPECIAL_RESTRICTED(): pass    # Only I can use these


class Command(object):
    def __init__(self, trigger, outfunc, bot, opcom=False, channels=[], chanblacklist=[], data=None, groups=[],
            repeatdelay=0, casesensitive=False, helpstring=None):

        self.trigger = trigger
        self.outfunc = outfunc
        self.bot = bot
        self.opcom = opcom
        self.channels = channels
        self.data = data
        self.repeatdelay = repeatdelay
        self.casesensitive = casesensitive
        self.helpstring = helpstring

        self.lastuse = None

        self.blacklist = chanblacklist
        self.groups = []

        if groups is None:
            return

        if type(groups) is str:
            self.groups.append(groups)
        else:
            self.groups.extend(groups)

    def __repr__(self):
        return "<%s: %s %s%s>" % (self.__class__, self.trigger, ('(mod command)' if self.opcom else ''), ("(channels: %s" % self.channels if len(self.channels) else ''))

    def _htime(self):
        return int(round(time.time()))

    def _issequence(self, item):
        return hasattr(item, '__iter__')

    def _checkdelay(self):
        # TODO: fix float/int comparison imprecision
        if self.lastuse is None: return True
        return int(self._htime() - self.lastuse) > self.repeatdelay

    def _dochecks(self, channel, user, msg, args):
        try:
            msg.split()[0]
        except:
            return BAD_MESSAGE

        if self.casesensitive:
            if self._issequence(self.trigger):
                if not msg.split[0] in self.trigger:
                    return WRONG_TRIGGER
            else:
                if not msg.split()[0] == self.trigger:
                    return WRONG_TRIGGER
        else:
            if self._issequence(self.trigger):
                if not msg.lower().split()[0] in [t.lower() for t in self.trigger]:
                    return WRONG_TRIGGER
            else:
                if not msg.lower().split()[0] == self.trigger.lower():
                    return WRONG_TRIGGER

        if channel in self.blacklist:
            return BAD_CHANNEL

        if self.channels and channel not in self.channels:
            return BAD_CHANNEL

        if user == 'imayhaveborkedit':
            return OK

        if 'broadcaster' in self.groups and user == channel:
            return OK

        if 'broadcaster' in self.groups and user != channel:
            return HOST_RESTRICTED
        
        if 'special' in self.groups and user != 'imayhaveborkedit':
            return SPECIAL_RESTRICTED

        if self.opcom and not self.bot.user_is_op(user):
            return OP_RESTRICTED

        if not self._checkdelay() and not self.bot.user_is_op(user):
            print "%s: Time Difference: %s, Delay: %s" % (self, time.time()-self.lastuse, self.repeatdelay)
            return DELAY_LOCKED

        return OK

    def enabledInChannel(self, channel):
        return channel in self.channels and channel not in self.blacklist

    def process(self, channel, user, message, args):
        err = self._dochecks(channel, user, message, args)
        if err != OK:
            return (None, err)

        self.lastuse = self._htime()

        if self.outfunc is not None:
            fout = self.outfunc(channel, user, message, args, self.data, self.bot)
            if fout is not None:
                return (fout, OK)
            else:
                return (None, None)
        else:
            raise RuntimeError("No function specified")


class SimpleCommand(Command):
    def __init__(self, trigger, output, bot, opcom = False, channels = [], chanblacklist = [], data = None, groups = [],
        repeatdelay = 0, casesensitive = False, prependuser = True, targeted = False, helpstring=None):

        self.trigger = trigger
        self.output = output
        self.bot = bot
        self.opcom = opcom
        self.channels = channels
        self.data = data
        self.repeatdelay = repeatdelay
        self.casesensitive = casesensitive
        self.prependuser = prependuser
        self.targeted = targeted
        self.helpstring = helpstring

        self.lastuse = None

        self.blacklist = chanblacklist
        self.groups = []

        if groups is None:
            return

        if type(groups) is str:
            self.groups.append(groups)
        else:
            self.groups.extend(groups)

    def process(self, channel, user, message, args):
        err = self._dochecks(channel, user, message, args)
        if err != OK:
            return (None, err)

        self.lastuse = self._htime()

        res = "%s%s"

        if self.prependuser:
            if self.targeted:
                if args:
                    res = res % (args[0] + ': ', self.output)
                else:
                    res = res % (user + ': ', self.output)
            else:
                res = res % (user + ': ', self.output)
        else:
            if self.targeted:
                if args:
                    res = res % (args[0] + ': ', self.output)
                else:
                    res = res % ('', self.output)
            else:
                res = res % ('', self.output)

        return res, OK


def get_process_output(incomm, shell=False, stripnls=False):
    out = subprocess.check_output(incomm, shell=shell, stderr=subprocess.STDOUT)
    return out if not stripnls else out.replace('\n','')

def setup(bot):
    pass

def alert(event):
    pass


#class JoinPartCommand(object):
#    def __init__(self, user, bot, joinfunc=None, partfunc=None, channels=[], data=None, groups = [], repeatdelay = 0):
#        self.user = user
#        self.bot = bot
#        self.joinfunc = joinfunc
#        self.partfunc = partfunc
#        self.channels = channels
#        self.data = data
#        self.groups = groups
#        self.repeatdelay = repeatdelay


class Commander(object):

    PERMISSION_SPECIAL = 0
    PERMISSION_BROADCASTER = 1
    PERMISSION_MODS = 2
    PERMISSION_SUBSCRIBERS = 3
    PERMISSION_ALL = 4
    PERMISSION_WHITELIST = 5
    PERMISSION_BLACKLIST = 6
    PERMISSION_WHITELIST_AND_BLACKLIST = 7

    def __init__(self, modulename, submodulepart='', eventtypes=['msg']):
        self.commands = []
        self.modulename = modulename
        self.eventtypes = eventtypes
        self.submodulepart = submodulepart

    @property
    def module(self):
        return self.modulename + '-' + self.submodulepart

    def addCommand(self, newcom):
        self.commands.append(newcom)

    def getCommand(self, trigger):
        for c in self.commands:
            if trigger in c.trigger:
                return c

    def removeCommand(self, trigger):
        self.commands.remove(self.getCommand(trigger))

    def processEvent(self, event):
        if event.etype in self.eventtypes: # This might need to change to allow for more diverse commands
            tstart = time.time()
            for comm in self.commands:
                t1 = time.time()
                output = comm.process(event.channel, event.user, event.data, self._getargs(event.data))
                t2 = time.time()
                if output[1] is comm.OK:
                    print "[%s] Output for %s: %s" % (self.modulename, comm.trigger, output[0])
                    print "[%s] Command time: %4.4fms, Total time: %4.4fms" % (self.modulename, (t2-t1)*1000,(t2-tstart)*1000)
                    event.bot.botsay(str(output[0]))

    def _getargs(self, msg):
        try:
            a = msg.split()
        except:
            return list()
        if len(a) == 1:
            return list()
        else:
            return a[1:]

# The code to generate the commands readme goes here somewhere, with raw command documentation or not