import sys
sys.dont_write_bytecode = True

import os, os.path
import time, Queue, traceback
from types import FunctionType

#########################

imported_modules = []
disabled_modules = []

modules_mtime = {}

user_blacklist = {}

IS_SETUP = False
DEBUG_OUTPUT = False
INFO_OUTPUT = True

RELOAD_MODULES = True

def doreload(bot):
    if RELOAD_MODULES:
        _manage_modules()

        for m in imported_modules:
            if os.path.getmtime(m.__file__) > modules_mtime[m]:
                _info("Reloading %s" % m.__name__)
                try:
                    reload(m)
                except Exception as e:
                    print 'I haz an error reloading module %s:' % m.__name__
                    print traceback.format_exc()
                else:
                    modules_mtime[m] = os.path.getmtime(m.__file__)
                    _init_module(m, bot)

    _debug('')


# This is the entry point for a bot using this
def setup(bot):
    import_time = time.time()

    _manage_modules()

    import_time2 = ((time.time() - import_time) * 1000)
    _debug("Imported modules in %4.4f ms" % import_time2)

    # Load settings from pickled dict or whatever

    _debug("Initializing modules...")
    _init_modules(bot)

    IS_SETUP = True


# This gets called by setup to gather
def _manage_modules():
    global imported_modules

    #print "Importing modules..."
    _debug('')

    try:
        import modules
        reload(modules)
    except ImportError as e:
        print "Cannot import modules."
        print traceback.format_exc()
    else:

        # TODO: Add __import__(channelname.py) or whatever

        fresh_imports = modules._m_imports

        for fi in fresh_imports:
            if getattr(fi, 'DISABLE_MODULE', False):
                _info("%s has been disabled and will be disregarded." % fi.__name__)
                fresh_imports.remove(fi)

        new_imports = list(set(fresh_imports) - set(imported_modules))
        removed_imports = list(set(imported_modules) - set(fresh_imports))

        if_issue = False
        for ni in new_imports:
            if not (type(getattr(ni, 'setup', False)) is FunctionType and type(getattr(ni, 'alert', False)) is FunctionType):

                if getattr(ni, 'LOAD_ORDER', None) is None:
                    ni.LOAD_ORDER = 1000
                    setattr(ni, 'LOAD_ORDER', 1000)
                    # Does this actually work?

                _info("%s is not a useable module and will not be imported." % ni.__name__)
                if_issue = True
                new_imports.remove(ni)

            elif getattr(ni, 'DISABLE_MODULE', False):
                _info("%s has been disabled and will not be imported." % ni.__name__)
                if_issue = True
                new_imports.remove(ni)

        if if_issue: _info('')

        imported_modules.extend(new_imports)
        imported_modules = list(set(imported_modules))

        imported_modules.sort(key=lambda x: x.LOAD_ORDER)

        if len(new_imports):
            _info("Importing %s new modules:" % len(new_imports))
            [_info('- %s'%m.__name__) for m in new_imports]
            _info('')

            for mm in imported_modules:
                modules_mtime[mm] = os.path.getmtime(mm.__file__)

        if len(removed_imports):
            _info("Removing %s modules:" % len(removed_imports))
            [_info('- %s'%m.__name__) for m in removed_imports]
            _info('')

            for mm in removed_imports:
                modules_mtime.pop(mm, None)


# This gets called after modules are imported to activate them
def _init_modules(bot):
    setup_time = 0

    for m in imported_modules:
        start_time = time.time()

        _init_module(m, bot)

        _debug('Done in', False)

        stop_time = ((time.time() - start_time) * 1000)
        _debug("%4.4f ms" % stop_time)

        setup_time += stop_time

    _debug("Total setup time: %4.4f ms\n" % setup_time)


def _init_module(m, bot):
    _debug("- %s..." % m.__name__,False)

    setup_result = True

    try:
        setup_result = m.setup(bot)
    except Exception as ee:
        print "Setup failure for %s" % m.__name__
        print traceback.format_exc()
        print

        setup_result = False

    if not setup_result and setup_result is not None:
        _debug("%s returned bad setup, will be disabled." % m.__name__)
        #Disable or whatever

    #print setup_result if setup_result is not None else 'Done in',



# This is what gets called by the bot to distribute events to modules
def event(channel, user, etype, data, bot, isop):
    if etype not in ['msg', 'timer']:
        print "Received event, %s: %s" % (etype, data)

    doreload(bot)

    event = IRCevent(bot, channel, user, etype, data, isop)

    # Extra logic goes here
    _process_event(event)


def _process_event(event):
    _debug("Preparing to dispatching %s event" % event.etype)

    # This needs to be improved to define event types
    #if _check_global_blacklist(event):
    #    print ""
    #    return

    #print "Dispatching event"

    for m in imported_modules:
        try:
            _debug("Alerting %s" % m.__name__)
            m.alert(event)
        except Exception as e:
            print "Alert error for %s: " % m.__name__
            print traceback.format_exc()


def _check_global_blacklist(event):
    return user in ('fidofidder', 'sage1447', 'jimbooob')


def _debug(o, nl=True):
    if DEBUG_OUTPUT:
        if nl:
            print o
        else:
            print o,

def _info(o, nl=True):
    if INFO_OUTPUT:
        if nl:
            print o
        else:
            print o,


def _pr(xx):
    print xx


class IRCevent(object):
    def __init__(self, bot, channel, user, etype, data, isop):
        self.bot = bot
        self.channel = channel
        self.user = user
        self.etype = etype
        self.data = data
        self.isop = isop

        self.time = time.time()
        self.htime = int(round(self.time))

    @staticmethod
    def glob(*evs):
        if len(evs) < 2:
            return evs
        if similar(evs[0], evs[1:]):
            return tuple(evs)

    @staticmethod
    def similar(ev1, *evx):
        et = ev1.etype.lower()
        return all(eti.etype.lower() == et for eti in evx)

    #def __eq__(self, other):
    #    return self.etype.lower() == other.etype.lower()
    #
    #def __ne__(self, other):
    #    return self.etype.lower() != other.etype.lower()

    #def __hash__(self):
    #    return hash(self.channel) + hash(self.user)*10 + hash(self.etype)*100 + hash(self.data)*1000 + hash(self.isop)*10000