import sys
sys.dont_write_bytecode = True

import requests, json

LOAD_ORDER = 80

root = 'https://api.twitch.tv/kraken/'

def _apiget(path):
    r = requests.get(root+path)
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


def setup(bot):
    return

def alert(event):
    return