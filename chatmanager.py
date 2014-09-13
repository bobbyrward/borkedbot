import sys, os
import time, Queue
from types import FunctionType

#########################

imported_modules = []
disabled_modules = []

user_blacklist = {}

DEBUG_OUTPUT = False
INFO_OUTPUT = True

#########################

# Either I have a file with enable/disable rules for modules, or I do it in __init__.py

# Ok I know what I need to do.  I need to check for file changes and then reload if needed.

RELOAD_MODULES = True

def doreload(bot):

    if RELOAD_MODULES: 

        _manage_modules()

        for m in imported_modules:
            # Add a os.path.getmtime check or something
            debug("Reloading %s..." % m.__name__)
            try:
                reload(m)
            except Exception as e:
                print 'I haz an error reloading module %s:' % m.__name__
                print e

        _init_modules(bot)


    debug('')

#########################


# This is the entry point for a bot using this
def setup(bot):
    import_time = time.time()
    
    _manage_modules()

    import_time2 = ((time.time() - import_time) * 1000)
    debug("Imported modules in %4.4f ms" % import_time2)

    # Load settings from pickled dict

    debug("Initializing modules...")
    _init_modules(bot)


# This gets called by setup to gather
def _manage_modules():
    global imported_modules

    #print "Importing modules..."
    debug('')

    try:
        import modules
        reload(modules)
    except ImportError as e:
        print "Cannot import modules."
        print e
    else:
        #old_imports = imported_modules
        fresh_imports = modules._m_imports
        
        new_imports = list(set(fresh_imports) - set(imported_modules))
        removed_imports = list(set(imported_modules) - set(fresh_imports))

        # I don't think anything here can break but i'll leave the try block in anyways
        try:
            ifunusable = False
            for ni in new_imports:
                if not (type(getattr(ni, 'setup', False)) is FunctionType and type(getattr(ni, 'alert', False)) is FunctionType):
                    info("%s is not a useable module and will not be imported." % ni.__name__)
                    ifunusable = True
                    new_imports.remove(ni)

            if ifunusable: info('')

            if len(new_imports):
                info("Importing %s new modules:" % len(new_imports))
                [info('- %s'%m.__name__) for m in new_imports]
                info('')
                
            if len(removed_imports):
                info("Removing %s modules:" % len(removed_imports))
                [info('- %s'%m.__name__) for m in removed_imports]
                info('')

            imported_modules.extend(new_imports)
            imported_modules = list(set(imported_modules))
        except Exception as e2:
            print "An unforseen error has occurred setting up imports:"
            print e2


# This gets called after modules are imported to activate them
def _init_modules(bot):
    setup_time = 0

    for m in imported_modules:
        debug("- %s..." % m.__name__,False)
        start_time = time.time()

        setup_result = True
        
        try:
            setup_result = m.setup(bot)
        except Exception as ee:
            print "Setup failure for %s" % m.__name__
            print ee
            print
            
            #exc_type, exc_obj, exc_tb = sys.exc_info()
            #fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            #print exc_type, fname, exc_tb.tb_lineno

            setup_result = False

        if not setup_result and setup_result is not None:
            debug("%s returned bad setup, will be disabled." % m.__name__)
            #Disable or whatever

        #print setup_result if setup_result is not None else 'Done in',
        debug('Done in', False)
        
        stop_time = ((time.time() - start_time) * 1000)
        debug("%4.4f ms" % stop_time)

        setup_time += stop_time

    debug("Total setup time: %4.4f ms\n" % setup_time)


# This is what gets called by the bot to distribute events to modules
def event(channel, user, etype, data, bot, isop):
    if etype != 'msg':
        print "Received event, %s: %s" % (etype, data)


    doreload(bot)

    event = IRCevent(bot, channel, user, etype, data, isop)

    # Extra logic goes here
    _process_event(event)


def _process_event(event):
    debug("Preparing to dispatching %s event" % event.etype)

    # This needs to be improved to define event types
    #if _check_global_blacklist(event):
    #    print ""
    #    return

    #print "Dispatching event"

    for m in imported_modules:
        try:
            debug("Alerting %s" % m.__name__)
            m.alert(event)
        except Exception as e:
            print "Alert error for %s: " % m.__name__
            print e


def _check_global_blacklist(event):
    return user in ('fidofidder', 'sage1447', 'jimbooob')


def debug(o, nl=True):
    if DEBUG_OUTPUT:
        if nl:
            print o
        else:
            print o,

def info(o, nl=True):
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