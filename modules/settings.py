import sys
sys.dont_write_bytecode = True

import os, cPickle

LOAD_ORDER = 50

datafilename = 'settings.data'

if not os.path.isfile(datafilename):
    with open(datafilename, 'w') as f:
        cPickle.dump(dict(), f)


def loadsettings():
    with open(datafilename, 'r') as f:
        data = cPickle.load(f)
    return data


def savesettings(data):
    with open(datafilename, 'w') as f:
        cPickle.dump(data, f)

def getdata(key):
    data = loadsettings()
    return data[key]

def setdata(key, value, announce=True):
    data = loadsettings()

    if data.has_key(key):
        if data[key] != value and announce:
            print "[Settings] Key %s changed: %s -> %s" % (key, data[key], value)
    
    if key not in data.keys():
        print "[Settings] Key added: %s (%s)" % (key, value)

    data[key] = value
    
    savesettings(data)

def trygetset(key, value, announce=True):
    data = loadsettings()
    try:
        return data[key]
    except:
        if key not in data.keys():
            print "[Settings] Key added: %s (%s)" % (key, value)

        data[key] = value
        
        savesettings(data)
        return data[key] 

def deldata(key, announce=True):
    data = loadsettings()
    if announce:
        print "[Settings] Key deleted: %s" % key
    data.pop(key)
    savesettings(data)

def setup(bot):
    return

def alert(event):
    return
