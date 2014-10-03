# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import os, time, json
import twitchapi, steamapi, settings

LOAD_ORDER = 30

def setup(bot):
    pass

def alert(event):
    # Sub alert
    if event.etype == 'twitchnotify':
        if event.channel in ['unsanitylive', 'monkeys_forever', 'superjoe', 'kizzmett']:
            if 'just subscribed!' in event.data:
                event.bot.botsay('SUB HYPE! PRAISE %s ヽ༼ຈل͜ຈ༽ﾉ' % event.data.split()[0].upper())

    
    if event.etype == 'msg' and 'http://steamcommumlity.com' in event.data and 'borkedbot' in event.bot.oplist:
        #event.bot.botsay(".ban %s" % event.user)
        event.bot.botsay("/ban %s" % event.user)
        event.bot.botsay("Get rekt idiot spambot.")


    # mmr updating
    if event.etype not in ['serverjoin', 'channeljoin', 'timer'] and event.channel == 'monkeys_forever':
        getmatchtimeout = settings.trygetset('monkeys_get_match_timeout', 60)
        lastmatchfetch = settings.trygetset('monkeys_last_match_fetch', time.time())
        
        if time.time() - int(getmatchtimeout) > float(lastmatchfetch):
            settings.setdata('monkeys_last_match_fetch', time.time())
            
            latestmatch = steamapi.getlastdotamatch(settings.getdata('monkeys_forever_dota_id'))
            previousmatch = settings.trygetset('monkeys_last_match', latestmatch)
    
            print "[Extra Events] Checking match IDs (%s:%s)" % (previousmatch['match_id'], latestmatch['match_id'])
            
            if previousmatch['match_id'] != latestmatch['match_id'] and str(latestmatch['lobby_type']) == '7':
                settings.setdata('monkeys_last_match', latestmatch)

                outputstring = "Solo: %s | Party: %s"

                print "[Extra Events] Updating mmr"
                #bot.botsay("Fetching data, one moment please.")
                #time.sleep(2)

                with open('/var/www/twitch/monkeys_forever/data', 'r') as d:
                    olddotadata = json.loads(d.readline())

                os.system('cd modules/node; nodejs mmr.js monkeys_forever %s' % settings.getdata('monkeys_forever_dota_id'))

                with open('/var/www/twitch/monkeys_forever/data', 'r') as d:
                    dotadata = json.loads(d.readline())

                old_mmr_s = str(olddotadata['gameAccountClient']['soloCompetitiveRank'])
                old_mmr_p = str(olddotadata['gameAccountClient']['competitiveRank'])

                new_mmr_s = str(dotadata['gameAccountClient']['soloCompetitiveRank'])
                new_mmr_p = str(dotadata['gameAccountClient']['competitiveRank'])

                mmr_s_change = str(int(new_mmr_s) - int(old_mmr_s))
                mmr_p_change = str(int(new_mmr_p) - int(old_mmr_p))

                if int(mmr_s_change) >= 0: mmr_s_change = '+' + mmr_s_change
                if int(mmr_p_change) >= 0: mmr_p_change = '+' + mmr_p_change

                newmmrstring = outputstring % ('%s (%s)' % (new_mmr_s, mmr_s_change), '%s (%s)' % (new_mmr_p, mmr_p_change))
                event.bot.botsay("Monkeys has finished a game.  http://www.dotabuff.com/matches/%s Updated mmr: %s" % (latestmatch['match_id'], newmmrstring))
                print "Monkeys has finished a game.  http://www.dotabuff.com/matches/%s  Updated mmr: %s" % (latestmatch['match_id'], newmmrstring)

    
    if event.etype not in ['serverjoin', 'channeljoin', 'timer'] and event.channel == 'kizzmett':
        getmatchtimeout = settings.trygetset('kizzmett_get_match_timeout', 60)
        lastmatchfetch = settings.trygetset('kizzmett_last_match_fetch', time.time())
        
        if time.time() - int(getmatchtimeout) > float(lastmatchfetch):
            settings.setdata('kizzmett_last_match_fetch', time.time())
            
            latestmatch = steamapi.getlastdotamatch(settings.getdata('kizzmett_dota_id'))
            previousmatch = settings.trygetset('kizzmett_last_match', latestmatch)
    
            print "[Extra Events] Checking match IDs (%s:%s)" % (previousmatch['match_id'], latestmatch['match_id'])
            
            if previousmatch['match_id'] != latestmatch['match_id'] and str(latestmatch['lobby_type']) == '7':
                settings.setdata('kizzmett_last_match', latestmatch)

                outputstring = "Solo: %s | Party: %s"

                print "[Extra Events] Updating mmr"
                #bot.botsay("Fetching data, one moment please.")
                #time.sleep(2)

                with open('/var/www/twitch/kizzmett/data', 'r') as d:
                    olddotadata = json.loads(d.readline())

                os.system('cd modules/node; nodejs mmr.js kizzmett %s' % settings.getdata('kizzmett_dota_id'))

                with open('/var/www/twitch/kizzmett/data', 'r') as d:
                    dotadata = json.loads(d.readline())

                old_mmr_s = str(olddotadata['gameAccountClient']['soloCompetitiveRank'])
                old_mmr_p = str(olddotadata['gameAccountClient']['competitiveRank'])

                new_mmr_s = str(dotadata['gameAccountClient']['soloCompetitiveRank'])
                new_mmr_p = str(dotadata['gameAccountClient']['competitiveRank'])

                mmr_s_change = str(int(new_mmr_s) - int(old_mmr_s))
                mmr_p_change = str(int(new_mmr_p) - int(old_mmr_p))

                if int(mmr_s_change) >= 0: mmr_s_change = '+' + mmr_s_change
                if int(mmr_p_change) >= 0: mmr_p_change = '+' + mmr_p_change

                newmmrstring = outputstring % ('%s (%s)' % (new_mmr_s, mmr_s_change), '%s (%s)' % (new_mmr_p, mmr_p_change))
                event.bot.botsay("Kizzmett has finished a game.  http://www.dotabuff.com/matches/%s Updated mmr: %s" % (latestmatch['match_id'], newmmrstring))
                print "Kizzmett has finished a game.  http://www.dotabuff.com/matches/%s  Updated mmr: %s" % (latestmatch['match_id'], newmmrstring)

