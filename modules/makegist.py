# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import time
from github3 import login

# DISABLE_MODULE = True
LOAD_ORDER = 500

with open('github_gist', 'r') as f:
    apikey = f.readline()
del f

git = login(token=apikey)


def create(data, desc=None, filename=None, public=False):
    files = {
        filename: { 'content': data }
    }

    gist = git.create_gist(desc, files, public)
    return gist.html_url

def create_dota_playerinfo(channel, data, desc=None, public=False):
    return create(data, 'Player Data for %s at %s' % (channel, time.ctime()) if not desc else desc, 'PlayerData.md', public)


def setup(bot):
    return

def alert(event):
    return
