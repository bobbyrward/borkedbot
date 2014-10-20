import sys
sys.dont_write_bytecode = True

import os, time, json, subprocess, shlex
import steamapi, twitchapi, settings

LOAD_ORDER = 36

enabled_channels = {
    # channel name : (Display name, get mmr)
    'mynameisamanda': ('Amanda', False), 
    'kizzmett': ('Kizzmett', True),
    'monkeys_forever': ('Monkeys', True),
    'barnyyy': ('Barny', False)
}


def setup(bot):
    return

def alert(event):
    if event.etype == 'msg' and event.channel in enabled_channels.keys():
        r = latestBlurb(event.channel)
        if r is not None:
            event.bot.botsay(r)


def latestBlurb(channel):
    if checktimeout(channel):
        dotaid = settings.getdata('%s_dota_id' % channel)
        if dotaid is None:
            print "[Dota] No ID on record for %s.  I should probably sort this out." % channel
            return

        settings.setdata('%s_last_match_fetch' % channel, time.time(), announce=False)

        latestmatch = steamapi.getlastdotamatch(dotaid)
        previousmatch = settings.trygetset('%s_last_match' % channel, latestmatch)

        if previousmatch['match_id'] != latestmatch['match_id']:

            # Somewhere in here is where I do the logic to check if we've skipped a game or not

            print "[Dota] Match ID change found (%s:%s)" % (previousmatch['match_id'], latestmatch['match_id'])
            return getLatestGameBlurb(channel, dotaid, latestmatch, enabled_channels[channel][1] and str(latestmatch['lobby_type']) == '7')


def checktimeout(channel):
    if not twitchapi.is_streaming(channel):
        return False

    laststreamcheck = settings.trygetset('%s_last_is_streaming_check' % channel, time.time())
    streamchecktimeout = settings.trygetset('%s_is_streaming_timeout' % channel, 30)

    if time.time() - int(streamchecktimeout) > float(laststreamcheck):
        getmatchtimeout = settings.trygetset('%s_get_online_match_timeout' % channel, 20)
        settings.setdata('%s_last_is_streaming_check' % channel, time.time(), announce=False)

    getmatchtimeout = settings.trygetset('%s_get_match_timeout' % channel, 30)
    lastmatchfetch = settings.trygetset('%s_last_match_fetch' % channel, time.time())

    return time.time() - int(getmatchtimeout) > float(lastmatchfetch)


def getLatestGameBlurb(channel, dotaid, latestmatch=None, getmmr=False):
    if latestmatch is None:
        latestmatch = steamapi.getlastdotamatch(dotaid)

    settings.setdata('%s_last_match' % channel, latestmatch, announce=False)

    matchdata = steamapi.GetMatchDetails(latestmatch['match_id'])
    herodata = steamapi.GetHeroes()

    for p in matchdata['result']['players']:
        if str(p['account_id']) == str(dotaid):
            playerdata = p
            break

    try:
        d_hero = [h['localized_name'] for h in herodata['result']['heroes'] if str(h['id']) == str(playerdata['hero_id'])][0]
    except:
        d_hero = 'Unknown Hero (this is a bug)'

    d_team = 'Radiant' if int(playerdata['player_slot']) < 128 else 'Dire'
    d_level = playerdata['level']

    d_kills = playerdata['kills']
    d_deaths = playerdata['deaths']
    d_assists = playerdata['assists']

    d_lasthits = playerdata['last_hits']
    d_denies = playerdata['denies']

    d_gpm = playerdata['gold_per_min']
    d_xpm = playerdata['xp_per_min']

    d_victory = 'Victory' if not (matchdata['result']['radiant_win'] ^ (d_team == 'Radiant')) else 'Defeat'

    finaloutput = "%s has %s a game.  http://www.dotabuff.com/matches/%s " % (
        enabled_channels[channel][0], 'won' if d_victory == 'Victory' else 'lost',  latestmatch['match_id'])

    extramatchdata = "| Level {} {} {} - KDA: {}/{}/{} - CS: {}/{} - GPM: {} - XPM: {}".format(
        d_level, d_team, d_hero, d_kills, d_deaths, d_assists, d_lasthits, d_denies, d_gpm, d_xpm)

    if getmmr:
        mmrstring = getMMRData(channel, dotaid)
        print "[Dota] " + finaloutput + mmrstring + extramatchdata
        return finaloutput + mmrstring + extramatchdata
    else:
        print "[Dota] " + finaloutput + extramatchdata
        return finaloutput + extramatchdata


def getMMRData(channel, dotaid):
    outputstring = "Updated MMR: Solo: %s | Party: %s "

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

    return outputstring % ('%s (%s)' % (new_mmr_s, mmr_s_change), '%s (%s)' % (new_mmr_p, mmr_p_change))
