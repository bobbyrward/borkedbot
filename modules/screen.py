# -*- coding: utf-8 -*-
import sys, os
sys.dont_write_bytecode = True



LOAD_ORDER = 700

_CHANNEL = ''

def setup(bot):
    global _CHANNEL
    _CHANNEL = bot.chan()

def alert(event):
    return


def usable(): # This might also work with cygwin or other systems but IDGAF
    return sys.platform.startswith('linux') and is_in_screen()

def is_in_screen():
    return os.environ['TERM'] == 'screen'

def get_screen_name():
    return os.environ['STY'].split('.')[1] # socket.name

def get_window_number():
    return int(os.environ['WINDOW'])

def _get_window_name():
    raise NotImplementedError("I don't even know if I can do this.")


def set_window_name(text):
    os.system('screen -S %s -p %s -X title "%s"' % (get_screen_name(), get_window_number(), text))

def reset_window_name():
    set_window_title(_CHANNEL)

def send_command(command, data, name=None, window=None):
    name = name or get_screen_name()
    window = window or get_window_number()
    os.system('screen -S %s -p %s -X %s %s' % (name, window, command, data))


def update_online_status(online=True, onlinetext=' - Online', offlinetext=' - Offline'):
    if not _CHANNEL: raise ValueError("No channel set.")
    wname = '%s%s' % (_CHANNEL, onlinetext if online else offlinetext)
    print '[Screen] Setting window %s name to %s' % (get_window_number(), wname)
    set_window_name(wname)