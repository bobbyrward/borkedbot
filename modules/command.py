# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import time, subprocess, random

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
    def __init__(self, trigger, outfunc, bot, opcom = False, channels = [], data = None, groups = [], 
        repeatdelay = 0, casesensitive = False):

        self.trigger = trigger
        self.outfunc = outfunc
        self.bot = bot
        self.opcom = opcom
        self.channels = channels
        self.data = data
        self.repeatdelay = repeatdelay
        self.casesensitive = casesensitive

        self.lastuse = None

        self.blacklist = []
        self.groups = []

        if groups is None: 
            return
        
        if type(groups) is type(' '):
            self.groups.append(groups)
        else:
            self.groups.extend(groups)

    def __repr__(self):
        return "<%s: %s %s%s>" % (self.__class__, self.trigger, ('(mod command)' if self.opcom else ''), ("(channels: %s" % self.channels if len(self.channels) else ''))

    def _htime(self):
        return int(round(time.time()))

    def _issequence(self, item):
        return hasattr(item, '__iter__')

    # Right so this doesn't actually work because the command gets reloaded every message...
    def _checkdelay(self):
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

        if 'special' in self.groups and user != 'imayhaveborkedit':
            return SPECIAL_RESTRICTED

        if user not in self.bot.oplist and self.opcom:
            return OP_RESTRICTED

        if not self._checkdelay():
            return DELAY_LOCKED

        if len(self.channels) > 0 and channel not in self.channels + ['borkedbot']:
            return BAD_CHANNEL

        return OK


    def enabledInChannel(self, channel):
        return channel in self.channels and channel not in self.blacklist

    def process(self, channel, user, message, args):
        err = self._dochecks(channel, user, message, args)
        if err != OK:
            return [None, err]

        self.lastuse = self._htime()

        if self.outfunc is not None:
            return [self.outfunc(channel, user, message, args, self.data, self.bot), OK]
        else: 
            raise RuntimeError("No function specified")


class SimpleCommand(Command):
    def __init__(self, trigger, output, bot, opcom = False, channels = [], data = None, groups = [], 
        repeatdelay = 0, casesensitive = False, prependuser = True, targeted = False):

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

        self.lastuse = None
        
        self.blacklist = []
        self.groups = []

        if groups is None: 
            return
        
        if type(groups) is type(' '):
            self.groups.append(groups)
        else:
            self.groups.extend(groups)
        

    def process(self, channel, user, message, args):
        err = self._dochecks(channel, user, message, args)
        if err != OK:
            return [None, err]

        self.lastuse = self._htime()
    
        res = "%s%s"

        if self.prependuser:
            if self.targeted:
                if len(args):
                    res = res % (args[-1:][0] + ': ', self.output)
                else:
                    res = res % (user + ': ', self.output)
            else:
                res = res % (user + ': ', self.output)
        else:
            if self.targeted:
                if len(args):
                    res = res % (args[-1:][0] + ': ', self.output)
                else:
                    res = res % ('', self.output)
            else:
                res = res % ('', self.output)


        return [res, OK]


class JoinPartCommand(object):
    def __init__(self, user, bot, joinfunc=None, partfunc=None, channels=[], data=None, groups = [], repeatdelay = 0):
        self.user = user
        self.bot = bot
        self.joinfunc = joinfunc
        self.partfunc = partfunc
        self.channels = channels
        self.data = data
        self.groups = groups
        self.repeatdelay = repeatdelay



def get_process_output(incomm, shell=False, stripnls=False):
    out = subprocess.check_output(incomm, shell=shell)
    return out if not stripnls else out.replace('\n','')

def setup(bot):
    pass

def alert(event):
    pass