import sys
sys.dont_write_bytecode = True

import os, time, json, subprocess, shlex
import steamapi, twitchapi, settings

LOAD_ORDER = 35

enabled_channels = {'monkeys_forever': 'Monkeys', 'kizzmett': 'Kizzmett'}

def setup(bot):
    # checks?
    return

def alert(event):
    if event.etype == 'msg' and event.channel in enabled_channels.keys():
        r = mmr(event.channel)
        if r is not None:
            event.bot.botsay(r)


def mmr(channel):
    if checktimeout(channel):
        settings.setdata('%s_last_match_fetch' % channel, time.time(), announce=False)
        
        dotaid = settings.getdata('%s_dota_id' % channel)

        if dotaid is None:
            print "[MMR] No ID on record for %s.  I should probably sort this out." % channel
            return

        latestmatch = steamapi.getlastdotamatch(dotaid)
        previousmatch = settings.trygetset('%s_last_match' % channel, latestmatch)

        
        if previousmatch['match_id'] != latestmatch['match_id'] and str(latestmatch['lobby_type']) == '7':
            print "[MMR] Match ID change found (%s:%s)" % (previousmatch['match_id'], latestmatch['match_id'])
            settings.setdata('%s_last_match' % channel, latestmatch, announce=False)

            matchdata = steamapi.GetMatchDetails(latestmatch['match_id'])

            for p in matchdata['result']['players']:
               if int(p['account_id']) == 86811043:
                   playerdata = p
                   break

            dota_gpm = playerdata['gold_per_min']
            dota_xpm = playerdata['xp_per_min']

            dota_level = playerdata['level']

            dota_kills = playerdata['kills']
            dota_deaths = playerdata['deaths']
            dota_assists = playerdata['assists']

            dota_lasthits = playerdata['last_hits']
            dota_denies = playerdata['denies']

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

            extramatchdata = " | KDA: %s/%s/%s | CS: %s/%s | GPM: %s | XPM: %s"

            finaloutput = "%s has finished a game.  http://www.dotabuff.com/matches/%s  Updated mmr: %s" % (enabled_channels[channel], latestmatch['match_id'], newmmrstring)

            print "[MMR] " + finaloutput + extramatchdata
            return finaloutput

def checktimeout(channel):
    laststreamcheck = settings.trygetset('%s_last_is_streaming_check' % channel, time.time())
    streamchecktimeout = settings.trygetset('%s_is_streaming_timeout' % channel, 30)
    
    if time.time() - int(streamchecktimeout) > float(laststreamcheck):
        if twitchapi.is_streaming(channel):
           getmatchtimeout = settings.trygetset('%s_get_online_match_timeout' % channel, 20)
        else:
           getmatchtimeout = settings.trygetset('%s_get_offline_match_timeout' % channel, 90)

        settings.setdata('%s_last_is_streaming_check' % channel, time.time(), announce=False)

    getmatchtimeout = settings.trygetset('%s_get_match_timeout' % channel, 30)
    lastmatchfetch = settings.trygetset('%s_last_match_fetch' % channel, time.time())
    
    return time.time() - int(getmatchtimeout) > float(lastmatchfetch)
