import sys
sys.dont_write_bytecode = True

import json, zerorpc
# import settings

LOAD_ORDER = 36

zrpc = zerorpc.Client()

def setup(bot):
    zrpc.connect('tcp://127.0.0.1:29390')

def alert(event):
    return

def status():
    return zrpc.status()

def updateMMR(channel, chid):
    zrpc.launchdota()
    try:
        return zrpc.updatemmr(channel, chid)
    except Exception as e:
        print e
        return False

# Set up wrapping code and expose functions as essentially wrappers 
# and probably include a raw eval function for testing or whatever