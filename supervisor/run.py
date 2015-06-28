import sys, os, time, logging, rpyc
import supervisor

from collections import deque
from rpyc.utils.server import ThreadedServer

sys.dont_write_bytecode = True
logging.basicConfig()



'''
This will be the file that runs the code from the server
so it can be reloaded without killing the server

Reloading will reset variables back to default but that
may not be a problem if I do some trickery

I have no idea what happens if it gets reloaded when a
function is running
'''


# node server: 29390
# supervisor:  29389

class BorkedbotSupervisorService(rpyc.Service):
    sv_list = {}

    def __init__(self, conn):
        rpyc.Service.__init__(self, conn)
        self.connid = conn._config['connid']
        print '[%s] Connection established' % self.connid
        self.botchannel = None
        self.bot = None
        self.codebase = supervisor.BorkedbotSupervisorCodebase(self)
        self.mailqueue = deque()

    def _rpyc_getattr(self, name):
        if name == 'codebase':
            self.reload_codebase()
        return getattr(self, name)

    # def on_connect(self):
        # print 'server:', self._conn._config['connid'], 'connect'

    def on_disconnect(self):
        self.codebase.cprint('Disconnect')

        if self.botchannel in self.sv_list:
            self.codebase.cprint('Deleting bot')
            self.sv_list.pop(self.botchannel) # .do_something_else()?
            print
            self.bot = None

    def init_bot(self, bot):
        print 'Initalizing bot for channel', bot.chan()
        print

        try:
            self.botchannel = bot.chan()
            self.sv_list[bot.chan()] = self
            self.bot = bot
        except Exception as e:
            print 'Bot init failed:', e
            # What do we do now since it failed... disconnect?

    def reload_codebase(self):
        reload(supervisor)
        self.codebase = supervisor.BorkedbotSupervisorCodebase(self)

    def get_bot_supervisors(self):
        return self.sv_list.values()

    def get_mail(self):
        if len(self.mailqueue):
            return self.mailqueue.popleft()

    def has_new_mail(self):
        return bool(len(self.mailqueue))

    def send_mail(self, datatype, data, channel=None):
        if channel is None: channel = self.botchannel
        self.sv_list[channel].mailqueue.append((datatype, data))



def dump_object_attr_info(thing, level=1):
    print '%s.%s' % (thing.__class__.__module__, thing.__class__.__name__)

    for item in dir(thing):
        print '  .%s' % item
        print '    Type:', type(getattr(thing, item))
        print '    Content:\n     ', getattr(thing, item)
        print

if __name__ == '__main__':
    print 'creating server'
    srvr = ThreadedServer(BorkedbotSupervisorService, port=29389, protocol_config = {'allow_all_attrs': True, 'allow_setattr': True, 'allow_delattr': True})

    print 'starting server'
    try:
        srvr.start()
    except KeyboardInterrupt:
        print 'Keyboard break'
    finally:
        print 'Server shut down'
