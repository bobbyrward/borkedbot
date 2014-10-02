import sys
sys.dont_write_bytecode = True

import requests, json, settings

LOAD_ORDER = 90

root = 'https://api.steampowered.com/'

with open('apikey', 'r') as f:
    apikey = f.readline()

DOTA_MATCH_TYPES = {
    -1: 'Invalid',
    0: 'Public matchmaking',
    1: 'Practice',
    2: 'Tournament',
    3: 'Tutorial',
    4: 'Co-op with bots',
    5: 'Team match',
    6: 'Solo Queue',
    7: 'Ranked',
    8: 'Solo Mid 1vs1'
}


def _apiget(path):
    return requests.get(root+path).json()

def get(path='', key=None):
    return _apiget(path) if not key else _apiget(path)[key]

def getlastdotamatch(idnum):
    return _apiget('IDOTA2Match_570/GetMatchHistory/V001/?key=%s&matches_requested=1&account_id=%s' % (apikey,idnum))['result']['matches'][0]

def setup(bot):
    return

def alert(event):
    return