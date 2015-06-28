import sys, os, time, math, random, re, redis, requests, json, rpyc
sys.dont_write_bytecode = True


'''
This will basically be the manager/central communication server for python code
for running tasks that cannot be done with multiple bots or condensing multiple
similar requests into one.  Additionally, there will be a way to send messages
to other running bots.
'''


# Maybe put this in the module file and have the client service be the codebase instead?
class BorkedbotSupervisorCodebase(object):
    class MAILTYPES(object):
        CHAT_MESSAGE = 'chatmsg'

    def __init__(self, supervisor):
        self.supervisor = supervisor

    def mass_print(self, consoletext):
        for sv in self.supervisor.get_bot_supervisors():
            sv.reload_codebase()
            sv.codebase.cprint(consoletext)
        print

    def cprint(self, message):
        print '[%s%s] %s' % (
            self.supervisor._conn._config['connid'],
            ':'+self.supervisor.botchannel if self.supervisor.botchannel else '',
            message)

    def mass_chat_message(self, message, channels=None):
        if not channels:
            self.mass_print('Sending mass chat message mail')
            for sv in self.supervisor.get_bot_supervisors():
                sv.reload_codebase()
                sv.send_mail(self.MAILTYPES.CHAT_MESSAGE, message)
        else:
            for ch in channels:
                try:
                    self.supervisor.sv_list.get(ch)
                except:
                    self.cprint('Skipping channel',ch)
                    continue
                self.supervisor.sv_list[ch].codebase.cprint('Sending mass chat message mail')
                self.supervisor.sv_list[ch].reload_codebase()
                self.supervisor.send_mail(self.MAILTYPES.CHAT_MESSAGE, message, ch)
        print


