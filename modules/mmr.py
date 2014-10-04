import sys
sys.dont_write_bytecode = True

import os, time, json
import steamapi, settings

LOAD_ORDER = 35

enabled_channels = {'monkeys_forever': 'Monkeys', 'kizzmett': 'Kizzmett'}

def setup(bot):
    # checks?
    return

def alert(event):
    if event.etype == 'msg' and event.channel in enabled_channels.keys():
        r = mmr(event.channel, enabled_channels[event.channel])
        if r is not None:
            event.bot.botsay(r)


def mmr(channel, name):
    getmatchtimeout = settings.trygetset('%s_get_match_timeout' % channel, 60)
    lastmatchfetch = settings.trygetset('%s_last_match_fetch' % channel, time.time())
    
    if time.time() - int(getmatchtimeout) > float(lastmatchfetch):
        settings.setdata('%s_last_match_fetch' % channel, time.time(), False)
        
        dotaid = settings.getdata('%s_dota_id' % channel)

        if dotaid is None:
            print "[MMR] No ID on record for %s.  I should probably sort this out." % channel
            return

        latestmatch = steamapi.getlastdotamatch(dotaid)
        previousmatch = settings.trygetset('%s_last_match' % channel, latestmatch)

        #print "[MMR] Checking match IDs (%s:%s)" % (previousmatch['match_id'], latestmatch['match_id'])
        
        if previousmatch['match_id'] != latestmatch['match_id'] and str(latestmatch['lobby_type']) == '7':
            settings.setdata('%s_last_match' % channel, latestmatch)

            outputstring = "Solo: %s | Party: %s"

            print "[MMR] Updating mmr"

            with open('/var/www/twitch/%s/data' % channel, 'r') as d:
                olddotadata = json.loads(d.readline())

            os.system('cd modules/node; nodejs mmr.js %s %s' % (channel, dotaid))

            with open('/var/www/twitch/%s/data' % channel, 'r') as d:
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
            print "[MMR] %s has finished a game.  http://www.dotabuff.com/matches/%s  Updated mmr: %s" % (name, latestmatch['match_id'], newmmrstring)
            return "%s has finished a game.  http://www.dotabuff.com/matches/%s Updated mmr: %s" % (name, latestmatch['match_id'], newmmrstring)