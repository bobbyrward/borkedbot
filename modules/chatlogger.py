import time, datetime
import os


def setup(bot):
    pass

def alert(event):
    if event.etype == 'msg':
        log(event.user, event.channel, event.data)

def formatdate():
    now = datetime.date.today()
    return "["+" ".join([now.strftime("%A")[0:3], now.strftime("%B")[0:3], now.strftime("%d"), datetime.datetime.now().strftime("%H:%M:%S"), time.tzname[0], now.strftime("%Y")])+"] "

def log(user, channel, msg, logstdout = True):
    logpath = "/var/www/twitch/%s/chat/" % channel.strip('#')
    if not os.path.isfile(logpath + "log.txt"): 
        print "Creating log file for " + channel
        if not os.path.isdir(logpath): os.makedirs(logpath)
    
    if logstdout:
        print formatdate() + "[" + channel + "]", user + ":", msg
    
    with open(logpath + "log.txt", 'a+') as f:
        f.write(formatdate() + user +": " +  msg + "\n")
