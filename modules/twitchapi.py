import requests, json

LOAD_ORDER = 80

root = 'https://api.twitch.tv/kraken/'

def _apiget(path):
    return requests.get(root+path).text

def _convertjson(j):
    return json.loads(j)

def get(path='', key=None):
    return _convertjson(_apiget(path)) if not key else _convertjson(_apiget(path))[key]


def setup(bot):
	return

def alert(event):
	return