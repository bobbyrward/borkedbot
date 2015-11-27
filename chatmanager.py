import sys
sys.dont_write_bytecode = True

import os, os.path
import time, Queue, traceback
from types import FunctionType
from twisted.internet import reactor, threads

#########################

imported_modules = []
disabled_modules = []

modules_mtime = {}

IS_SETUP = False
DEBUG_OUTPUT = False
INFO_OUTPUT = True

RELOAD_MODULES = True

def doreload(bot):
    if RELOAD_MODULES:
        _manage_modules()

        for m in imported_modules:
            try:
               os.path.getmtime(m.__file__) > modules_mtime[m]
            except:
                continue 
                #TODO: FIX unimported modules not reloading

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
        print "[ChatManager] Cannot import modules."
        print traceback.format_exc()
    else:

        # TODO: Add __import__(channelname.py) or whatever

        fresh_imports = modules._m_imports

        for fi in fresh_imports:
            if getattr(fi, 'DISABLE_MODULE', False):
                _debug("%s has been disabled and will be disregarded." % fi.__name__)
                fresh_imports.remove(fi)

        if_issue = False
        for fi in fresh_imports:
            if not (type(getattr(fi, 'setup', False)) is FunctionType and type(getattr(fi, 'alert', False)) is FunctionType):

                if getattr(fi, 'LOAD_ORDER', None) is None:
                    fi.LOAD_ORDER = 1000
                    setattr(fi, 'LOAD_ORDER', 1000)
                    # Does this actually work?

                _debug("%s is not a useable module and will not be imported." % fi.__name__)
                if_issue = True
                fresh_imports.remove(fi)

            if getattr(fi, 'DO_NOT_ALERT', False):
                _debug("%s has been disabled and will not be imported." % fi.__name__)
                if_issue = False
                fresh_imports.remove(fi)

                # TODO: For some reason, if it finds this, it doesn't change when its removed, might need to check the init file

        if if_issue: _debug('')

        new_imports = list(set(fresh_imports) - set(imported_modules))
        removed_imports = list(set(imported_modules) - set(fresh_imports))
        # These shouldn't even be mentioned, just removed from the import list and ignored

        imported_modules.extend(new_imports)
        imported_modules = list(set(imported_modules) - set(removed_imports))

        # print 'Imported modules : %s' % [nnn.__name__ for nnn in imported_modules]; print

        imported_modules.sort(key=lambda x: x.LOAD_ORDER)
        new_imports.sort(key=lambda x: x.LOAD_ORDER)

        if len(new_imports):
            _info("Importing %s new modules:" % len(new_imports))
            [_info('- %s' % m.__name__) for m in new_imports]
            print

            for mm in imported_modules:
                modules_mtime[mm] = os.path.getmtime(mm.__file__)

        if len(removed_imports):
            _info("Removing %s modules:" % len(removed_imports))
            [_info('- %s' % m.__name__) for m in removed_imports]
            print

            for mm in removed_imports:
                if mm in imported_modules:
                    try:
                        del modules_mtime[mm]
                    except:
                        _info("Error removing module %s" % mm)


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
        print "[ChatManager] Setup failure for %s" % m.__name__
        print traceback.format_exc()
        print

        setup_result = False

    if not setup_result and setup_result is not None:
        _debug("%s returned bad setup, will be disabled." % m.__name__)
        #Disable or whatever

    #print setup_result if setup_result is not None else 'Done in',


# This is what gets called by the bot to distribute events to modules
def event(channel, user, etype, data, bot, isop, extratags=[]):
    if etype not in ['msg', 'timer', 'action', 'botsay']:
        print "[ChatManager] Received event, %s: %s%s" % (etype, data, ' (%s)' % extratags if extratags else '')

    doreload(bot)

    event = IRCevent(bot, channel, user, etype, data, isop, extratags)

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
            # m.alert(event)
            threads.deferToThread(m.alert, event)
        except Exception as e:
            if 'secret' not in m.__name__:
                print "[ChatManager] Alert error for %s: " % m.__name__
                print traceback.format_exc()


def _debug(o, nl=True):
    if DEBUG_OUTPUT:
        if nl:
            print o
        else:
            print o,

def _info(o, nl=True):
    if INFO_OUTPUT:
        if nl:
            print '[ChatManager] %s' % o
        else:
            print '[ChatManager] %s' % o,

def _pr(xx):
    print xx


# TODO: add some sort of log function for stdout replacement/enhancement
class IRCevent(object):
    def __init__(self, bot, channel, user, etype, data, isop, tags=[]):
        self.bot = bot
        self.channel = channel
        self.user = user
        self.etype = etype
        self.data = data
        self.isop = isop
        self.tags = tags

        self.time = time.time()
        self.htime = int(round(self.time))

    def special(self, tag):
        return tag in self.tags

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
