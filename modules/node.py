import sys
sys.dont_write_bytecode = True

import json, zerorpc
import settings

LOAD_ORDER = 36

zrpc = zerorpc.Client()
zrpc.connect('tcp://127.0.0.1:29390')

def setup(bot):
    # zrpc.connect('tcp://127.0.0.1:29390')
    pass

def alert(event):
    return

#####################

def restart():
    return zrpc.shutdown()

def status():
    return zrpc.status()

def launch_dota():
    return zrpc.launchdota()

def close_dota():
    return zrpc.closedota()

def gc_status():
    return zrpc.GCready()

def get_enum(name=None):
    return zrpc.getenum(name)

def get_mm_stats():
    return zrpc.getmmstats()

########

def updateMMR(channel, chid, autolaunch=True):
    if autolaunch:
        zrpc.launchdota()

    try:
        return zrpc.updatemmr(channel, chid)
    except Exception as e:
        print e
        return False


def verify_code(channel, code):
    return zrpc.verifycheck(channel, code)

def delete_key(channel):
    return zrpc.clearkey(channel)


########

def create_lobby(gameName, gameMode, password=None, serverRegion=None):
    cid = settings.getdata('current_lobby_id', coerceto=str)

    if cid != '0':
        return None

    l_id = zrpc.createlobby(gameName, password, serverRegion, gameMode)
    settings.setdata('current_lobby_id', str(l_id))

    return l_id

def start_lobby():
    zrpc.startlobby()

def leave_lobby():
    settings.setdata('current_lobby_id', '0')
    return zrpc.leavelobby()

def get_lobby():
    return settings.getdata('current_lobby_id', coerceto=str)


'''
game_name           : str, lobby title.
server_region       : int, Use the server region enum.
game_mode           : int, Use the game mode enum.
allow_cheats        : bool, allow cheats.
fill_with_bots      : bool, Fill available slots with bots?
allow_spectating    : bool, Allow spectating?
pass_key            : str, Password.
series_type         : int, Use the series type enum.
radiant_series_wins : int, Best of 3 for example, # of games won so far.
dire_series_wins    : int, Best of 3 for example, # of games won so far.
allchat             : bool, Enable all chat?
'''

def config_lobby(
    game_name = None, server_region = None, game_mode = None, allow_cheats = None, 
    fill_with_bots = None, allow_spectating = None, pass_key = None, series_type = None, 
    radiant_series_wins = None, dire_series_wins = None, allchat = None): 
    # This doesn't work yet

    args = {k:v for k,v in locals().items() if v is not None}
    return False

def kick_lobby(userid):
    return zrpc.lobby_kick(userid)

def shuffle_lobby():
    return zrpc.lobby_shuffle()

def flip_lobby():
    return zrpc.lobby_flip()

########

def join_chat(chatname, ctype=None):
    return zrpc.joinchat(chatname, ctype)

def leave_chat(chatname):
    return zrpc.leavechat(chatname)

def chat(channelname, message):
    return zrpc.chat(channelname, message)

def get_chats():
    return zrpc.getchats()
