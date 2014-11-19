import sys
sys.dont_write_bytecode = True

import time, dill
import settings
from twisted.internet import task, threads

LOAD_ORDER = 31

recurring_domain = None
the_channel = None

def setup(bot):
    global recurring_domain
    global the_channel
    recurring_domain = 'recurring_events_for_%s' % bot.chan()
    the_channel = bot.chan()

def alert(event):
    return

# TODO: switch to key name settings reqest to allow for easy changing
def _online_check_wrapper(channel, message, bot):
    import twitchapi
    print '[Recurring] Doing call'
    if twitchapi.is_streaming(channel):
        bot.botsay(message)


def register_new_recurring(bot, name, message, timeout, duration=None, autostart=True):
    if settings.exists(name, recurring_domain):
        return False

    timeout = int(timeout)
    message = str(message)

    recurtask = task.LoopingCall(_online_check_wrapper, the_channel, message, bot)
    recurringid = id(recurtask)

    settings.setdata(name, recurringid, recurring_domain)
    settings.setdata(name + '_data', (timeout, message, time.time()), recurring_domain)

    print '[Recurring] Creating recurring %s for %s' % (name, the_channel)

    if autostart:
        recurtask.start(timeout, False)

    return True

def delete_recurring(name):
    if not settings.exists(name, recurring_domain):
        return False

    print '[Recurring] Deleting %s for %s' % (name, the_channel)
    # WHAT A FUCKING WEIRD WAY TO DO THIS
    try:
        rtask = _get_recurring(name)
        rtask.stop()
        del rtask
    except:
        pass

    settings.deldata(name, recurring_domain)
    settings.deldata(name + '_data', recurring_domain)

    return True

def is_resurring_running(name):
    if not settings.exists(name, recurring_domain):
        return None

    return _get_recurring(name).running

def list_recurring(channel=None):
    channel = channel or the_channel

    return settings.dumpkeys('recurring_events_for_%s' % channel)


def start_recurring(name):
    if not settings.exists(name, recurring_domain):
        return False

    recurring = _get_recurring(name)
    recurring.start(settings.getdata(name + '_data', recurring_domain)[0], True)

    print '[Recurring] Starting %s for %s' % (name, the_channel)
    return True

def stop_recurring(name):
    if not settings.exists(name, recurring_domain):
        return False

    recurring = _get_recurring(name)
    recurring.stop()

    print '[Recurring] Stopping %s for %s' % (name, the_channel)
    return True


def skip_recurring(name):
    if not settings.exists(name, recurring_domain):
        return False

    recurring = _get_recurring(name)
    recurring.reset()

    print '[Recurring] Skipping %s for %s' % (name, the_channel)
    return True


def set_timeout(name, newtimeout, imediatestart=True):
    if not settings.exists(name, recurring_domain):
        return False

    recurring = _get_recurring(name)
    oldtimeout, message, createdat = settings.getdata(name + '_data', recurring_domain)

    recurring.stop()
    recurring.start(newtimeout, imediatestart)

    settings.setdata(name + '_data', (newtimeout, message, createdat), recurring_domain)

    print '[Recurring] Changed %s timeout: %s -> %s, %simediate' % (name, oldtimeout, newtimeout, '' if imediatestart else 'not ')
    return True


def _get_recurring(name):
    return dill.detect.at(int(settings.getdata(name, recurring_domain)))


'''
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
'''