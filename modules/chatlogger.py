import sys
sys.dont_write_bytecode = True

import os
import time
import datetime

LOAD_ORDER = 10

def setup(bot):
    pass

def alert(event):
    if event.etype in ['msg','action', 'botsay']:
        log(event.user, event.channel, event.data, event.user in event.bot.oplist, event.etype == 'action')

def formatdate():
    now = datetime.date.today()
    return "["+" ".join([now.strftime("%A")[0:3], now.strftime("%B")[0:3], now.strftime("%d"), datetime.datetime.now().strftime("%H:%M:%S"), time.tzname[0], now.strftime("%Y")])+"]"

def log(user, channel, msg, isop, isaction = False, logstdout = True):
    logpath = "/var/www/twitch/%s/chat/" % channel
    if not os.path.isfile(logpath + "log.txt"): 
        print "Creating log file for " + channel
        if not os.path.isdir(logpath): os.makedirs(logpath)

    now = formatdate()

    if not isaction:
        outputformat = "%s [%s] <%s%s> %s"
        logfileformat = "%s %s: %s\n"
    else:
        outputformat = "%s [%s] *%s%s %s"
        logfileformat = "%s * %s %s\n"


    if logstdout:
        if user == channel:
            indicator = '@'
        elif isop:
            indicator = '+'
        else:
            indicator = ' '

        # print now + "[" + channel + "]", '<' + indicator + user + '>', msg
        print outputformat % (now, channel, indicator, user, msg)

    with open(logpath + "log.txt", 'a+') as f:
        # f.write(now + user +": " +  msg + "\n")
        try:
            f.write(logfileformat % (now, user, msg))
        except UnicodeEncodeError:
            print 'Error logging line:', msg
            print 'Attempting to decode'
            f.write(logfileformat % (now, user, msg.encode('utf8')))

