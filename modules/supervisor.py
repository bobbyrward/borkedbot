# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import rpyc

LOAD_ORDER = 1000


sv_con = None


class BorkedbotClientService(rpyc.Service):
    def _rpyc_getattr(self, name):
        return getattr(self, name)


def setup(bot):
    connect(bot)

def alert(event):
    check_connection(event.bot)
    check_mail(event.bot)


def check_connection(bot):
    if sv_con is None:
        connect(bot)
        return

    try:
        sv_con.ping()
    except:
        print '[Supervisor] Ping failed, reconnecting'
        try:
            connect(bot)
        except Exception as e:
            print e
            # print 'supervisor server is down'
            pass

def connect(bot):
    global sv_con
    # print 'connecting to bot'

    BorkedbotClientService.bot = bot
    sv_con = rpyc.connect('localhost', 29389, service=BorkedbotClientService, config={'allow_all_attrs': True, 'exposed_prefix': ''})
    sv_con.root.init_bot(bot)

    # print 'connected'

def check_mail(bot):
    mail = sv_con.root.get_mail()
    if mail is None: return
    print 'got new mail:', mail

    if mail[0] == sv_con.root.codebase.MAILTYPES.CHAT_MESSAGE:
        print 'sending chat message'
        bot.botsay(mail[1])
    else:
        print 'Discarding unknown mail:', mail

