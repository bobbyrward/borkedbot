import sys
sys.dont_write_bytecode = True

import time, dill
import settings
from twisted.internet import task, threads

LOAD_ORDER = 31

recurring_domain = None

def setup(bot):
    global recurring_domain
    recurring_domain = 'recurring_events_for_%s' % bot.chan()

def alert(event):
    return


def _online_check_wrapper(channel, message, onlyonline, bot):
    import twitchapi
    if onlyonline:
        if twitchapi.is_streaming(channel):
            bot.botsay(message)
    else:
        bot.botsay(message)


def register_new_recurring(bot, name, message, timeout, duration=None, autostart=True, onlywhileonline=True):
    if settings.exists(name, recurring_domain):
        return False

    timeout = int(timeout)
    message = str(message)

    recurtask = task.LoopingCall(_online_check_wrapper, recurring_domain.split('_')[-1], message, onlywhileonline, bot)
    recurringid = id(recurtask)

    settings.setdata(name, recurringid, recurring_domain)
    settings.setdata(name + '_data', (timeout, message, time.time()), recurring_domain)

    if autostart:
        recurtask.start(timeout, True)

    return True

def delete_recurring(name):
    if not settings.exists(name, recurring_domain):
        return False

    # WHAT A FUCKING WEIRD WAY TO DO THIS
    rtask = _get_recurring(name)
    rtask.stop()

    settings.deldata(name, recurring_domain)
    del rtask
    
    return True

def is_resurring_running(name):
    if not settings.exists(name, recurring_domain):
        return None

    return _get_recurring(name).running

def list_recurring(channel=None):
    channel = channel or recurring_domain.split('_')[-1]

    return settings.dumpkeys('recurring_events_for_%s' % channel)


def start_recurring(name):
    if not settings.exists(name, recurring_domain):
        return False

    recurring = _get_recurring(name)
    recurring.start(settings.getdata(name + '_data', recurring_domain)[0], True)

    return True

def stop_recurring(name):
    if not settings.exists(name, recurring_domain):
        return False

    recurring = _get_recurring(name)
    recurring.stop()

    return True


def skip_recurring(name):
    if not settings.exists(name, recurring_domain):
        return False

    recurring = _get_recurring(name)
    recurring.reset()

    return True


def _get_recurring(name):
    return dill.detect.at(int(settings.getdata(name, recurring_domain)))


class Recurring(object):
    def __init__(self, name, message, timeout, bot, duration=None, onlywhileonline=True):
        from twisted.internet import task

        self.name = name
        self.message = message
        self.input_timeout = timeout
        self.timeout = self._round5(timeout)
        self.bot = bot

        self.onlywhileonline = onlywhileonline
        if onlywhileonline:
            import twitchapi

        self.channel = bot.channel
        self.running = False

        self.recurtask = task.LoopingCall(self.occur)

    def __del__(self):
        self.recurtask.stop()

    def _round5(self, x):
        return int(5 * round(float(x)/5))

    def start_task(self):
        if self.running: return
        self.recurtask.start(self.timeout, False)
        self.running = True

    def stop_task(self):
        self.recurtask.stop()
        self.running = False

    def skip_task(self):
        self.recurtask.reset()

    def occur(self):
        if onlywhileonline:
            if twitchapi.is_streaming(self.channel):
                self.bot.botsay(str(message))
        else:
            self.bot.botsay(str(message))
