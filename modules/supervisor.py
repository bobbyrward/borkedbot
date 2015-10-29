# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import os
import rpyc

LOAD_ORDER = 1000

sv_con = None


class BorkedbotClientService(rpyc.Service):
    def _rpyc_getattr(self, name):
        return getattr(self, name)


class MailHandler(object):

    @staticmethod
    def handle(bot, mailtype, data):
        try:
            handler = getattr(MailHandler, '_' + mailtype)
            handler(bot, data)
        except:
            MailHandler._unknown(bot, (mailtype, data))

    @staticmethod
    def _chatmsg(bot, data):
        print 'sending chat message'
        bot.botsay(data)

    @staticmethod
    def _screen_update(bot, data):
        # print 'updating screen name status'
        import screen
        screen.update_online_status(data)

    @staticmethod
    def _screen_reset(bot, data):
        # print 'resetting screen name status'
        import screen
        screen.reset_window_name()

    @staticmethod
    def _screen_window_num_update(bot, data):
        os.environ['WINDOW'] = str(data)

    @staticmethod
    def _test(bot, data):
        print 'ok ' + data

    @staticmethod
    def _unknown(bot, data):
        print 'Discarding unknown mail: %s' % data


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
    print '[Supervisor] Got new mail:', mail

    MailHandler.handle(bot, mail[0], mail[1])

def send_mail(bot, x):
    pass