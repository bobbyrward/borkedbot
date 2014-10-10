import sys
sys.dont_write_bytecode = True

import requests, json

LOAD_ORDER = 80

root = 'https://api.twitch.tv/kraken/'

def _apiget(path):
    try:
        return requests.get(root+path).json()
    except Exception as e:
        print e


def get(path='', key=None):
    return _apiget(path) if not key else _apiget(path)[key]

def is_streaming(channel):
    return get('streams/%s' % channel, 'stream') is not None


def setup(bot):
    return

def alert(event):
    return