import sys
sys.dont_write_bytecode = True

import requests, json

LOAD_ORDER = 80

root = 'https://api.twitch.tv/kraken/'


def _apiget(path, root=root):
    # print root+path
    r = requests.get(root+path, timeout=4)
    r.raise_for_status()

    try:
        return r.json()
    except Exception as e:
        print r.status_code, r.reason
        print e



def get(path='', key=None):
    return _apiget(path) if not key else _apiget(path)[key]

def is_streaming(channel):
    return get('streams/%s' % channel, 'stream') is not None

def get_chatters(channel):
    r = requests.get('https://tmi.twitch.tv/group/user/%s/chatters' % channel, timeout=4)
    r.raise_for_status()
    return r.json()

def get_steam_id_from_twitch(name):
    try:
        return _apiget('channels/%s' % name, root='https://api.twitch.tv/api/')['steam_id']
    except:
        return None

def get_twitch_from_steam_id(steamid):
    #might need to resolve steamid
    try:
        return _apiget('steam/%s' % steamid, root='https://api.twitch.tv/api/')['name']
    except:
        return None

def setup(bot):
    return

def alert(event):
    return