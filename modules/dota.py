import sys
sys.dont_write_bytecode = True

import os, time, json, subprocess, shlex
import steamapi, twitchapi, settings

LOAD_ORDER = 36

enabled_channels = {'mynameisamanda': 'Amanda'}


def setup(bot):
    return

def alert(event):
    if event.etype == 'msg' and event.channel in enabled_channels.keys():
        r = latestgameblurb(event.channel)
        if r is not None:
            event.bot.botsay(r)


def latestgameblurb(channel):
    if checktimeout(channel) or True:
        print 'we made it past the check'
        settings.setdata('%s_last_match_fetch' % channel, time.time(), announce=False)

        dotaid = settings.getdata('%s_dota_id' % channel)

        if dotaid is None:
            print "[Dota] No ID on record for %s.  I should probably sort this out." % channel
            return

        latestmatch = steamapi.getlastdotamatch(dotaid)
        previousmatch = settings.trygetset('%s_last_match' % channel, latestmatch)

        if previousmatch['match_id'] != latestmatch['match_id']:# and str(latestmatch['lobby_type']) == '7':
            print "[Dota] Match ID change found (%s:%s)" % (previousmatch['match_id'], latestmatch['match_id'])
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

            d_level = playerdata['level']
            d_team = 'Radiant' if int(playerdata['player_slot']) < 128 else 'Dire'

            d_kills = playerdata['kills']
            d_deaths = playerdata['deaths']
            d_assists = playerdata['assists']

            d_lasthits = playerdata['last_hits']
            d_denies = playerdata['denies']

            d_gpm = playerdata['gold_per_min']
            d_xpm = playerdata['xp_per_min']

            d_victory = 'Victory' if not (matchdata['result']['radiant_win'] ^ (d_team == 'Radiant')) else 'Defeat'

            finaloutput = "%s has %s a game.  http://www.dotabuff.com/matches/%s" % ('won' if d_victory == 'Victory' else 'lost',enabled_channels[channel], latestmatch['match_id'])

            extramatchdata = " | Level {} {} {} - KDA: {}/{}/{} - CS: {}/{} - GPM: {} - XPM: {}".format(
                d_level, d_team, d_hero, d_kills, d_deaths, d_assists, d_lasthits, d_denies, d_gpm, d_xpm)

            print "[Dota] " + finaloutput + extramatchdata
            return finaloutput + extramatchdata


def checktimeout(channel):
    #if not twitchapi.is_streaming(channel):
    #    return False

    laststreamcheck = settings.trygetset('%s_last_is_streaming_check' % channel, time.time())
    streamchecktimeout = settings.trygetset('%s_is_streaming_timeout' % channel, 30)

    if time.time() - int(streamchecktimeout) > float(laststreamcheck):
        getmatchtimeout = settings.trygetset('%s_get_online_match_timeout' % channel, 20)

        # if twitchapi.is_streaming(channel):
        # else:
        #    getmatchtimeout = settings.trygetset('%s_get_offline_match_timeout' % channel, 90)

        settings.setdata('%s_last_is_streaming_check' % channel, time.time(), announce=False)

    getmatchtimeout = settings.trygetset('%s_get_match_timeout' % channel, 30)
    lastmatchfetch = settings.trygetset('%s_last_match_fetch' % channel, time.time())

    return time.time() - int(getmatchtimeout) > float(lastmatchfetch)
