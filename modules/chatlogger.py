import sys
sys.dont_write_bytecode = True

import os, time, datetime

LOAD_ORDER = 10

def setup(bot):
    pass

def alert(event):
    if event.etype in ['msg','action']:
        log(event.user, event.channel, event.data, event.user in event.bot.oplist)

def formatdate():
    now = datetime.date.today()
    return "["+" ".join([now.strftime("%A")[0:3], now.strftime("%B")[0:3], now.strftime("%d"), datetime.datetime.now().strftime("%H:%M:%S"), time.tzname[0], now.strftime("%Y")])+"] "

def log(user, channel, msg, isop, logstdout = True):
    logpath = "/var/www/twitch/%s/chat/" % channel
    if not os.path.isfile(logpath + "log.txt"): 
        print "Creating log file for " + channel
        if not os.path.isdir(logpath): os.makedirs(logpath)

    now = formatdate()

    if logstdout:
        if user == channel:
            indicator = '@'
        elif isop:
            indicator = '+'
        else:
            indicator = ' '

        print now + "[" + channel + "]", '<' + indicator + user + '>', msg

    with open(logpath + "log.txt", 'a+') as f:
        f.write(now + user +": " +  msg + "\n")
