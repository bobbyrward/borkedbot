import sys
sys.dont_write_bytecode = True

import os, cPickle, redis

LOAD_ORDER = 50

redisdb = redis.StrictRedis(db=3)


def getdata(key, domain='settings-global', coerceto=None):
    result = cPickle.loads(redisdb.hget(domain, key))

    if coerceto:
        return coerceto(result)
    else:
        return result

def setdata(key, value, domain='settings-global', announce=True):
    oldresult = cPickle.loads(redisdb.hget(domain, key))
    isnew = redisdb.hset(domain, key, cPickle.dumps(value))
    
    if isnew:
        print "[Settings] Key added: %s (%s)" % (key, value)
    elif announce:
        print "[Settings] Key %s changed: %s -> %s" % (key, oldresult, value)

def trygetset(key, value, domain='settings-global', coerceto=None, announce=True):
    if not redisdb.hexists(domain, key):
        print "[Settings] Key added: %s (%s)" % (key, value)
        setdata(key, value, domain, announce)

    return getdata(key, domain, coerceto)


def deldata(key, domain='settings-global', announce=True):
    if announce:
        print "[Settings] Key deleted: %s" % key
    redisdb.hdel(key)

def setup(bot):
    return

def alert(event):
    return
