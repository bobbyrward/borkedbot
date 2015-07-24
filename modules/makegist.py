# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import time, requests
from github3 import login

# DISABLE_MODULE = True
LOAD_ORDER = 500

with open('github_gist', 'r') as f:
    apikey = f.readline()
del f

git = login(token=apikey)


def create(data, desc=None, filename=None, public=False, shorten=False):
    files = {
        filename: { 'content': data }
    }

    gist = git.create_gist(desc, files, public)
    if shorten:
    	try:
    		return shorten_link(gist.html_url)
    	except Exception as e:
    		print '[Gist] Error:', e
    else:
    	return gist.html_url

def create_dota_playerinfo(channel, data, desc=None, public=False, shorten=False):
    return create(data, 'Player Data for %s at %s' % (channel, time.ctime()) if not desc else desc, 'PlayerData.md', public, shorten)

def shorten_link(url):
	r = requests.post('http://git.io', {'url':url})
	r.raise_for_status()
	print '[Gist] Shortened %s -> %s' % (url, r.headers['location'])
	return r.headers['location']

def setup(bot):
    return

def alert(event):
    return
