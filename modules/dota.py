import sys
sys.dont_write_bytecode = True

import os, time, json, subprocess, shlex
import steamapi, twitchapi, settings, node

LOAD_ORDER = 35

# enabled_channels = {
#     # channel name : (Display name, mmr enabled)
#     'monkeys_forever': (settings.getdata('%s_common_name' % 'monkeys_forever'), settings.getdata('%s_mmr_enabled' % 'monkeys_forever')),
#     'mynameisamanda': (settings.getdata('%s_common_name' % 'mynameisamanda'), settings.getdata('%s_mmr_enabled' % 'mynameisamanda')),
#     'kizzmett': (settings.getdata('%s_common_name' % 'kizzmett'), settings.getdata('%s_mmr_enabled' % 'kizzmett')),
#     'barnyyy': (settings.getdata('%s_common_name' % 'barnyyy'), settings.getdata('%s_mmr_enabled' % 'barnyyy'))
# }

enabled_channels = {ch:(settings.getdata('%s_common_name' % ch),settings.getdata('%s_mmr_enabled' % ch)) for ch in settings.getdata('dota_enabled_channels')}

STEAM_TO_DOTA_CONSTANT = 76561197960265728

def update_channels():
    global enabled_channels
    enabled_channels = {ch:(settings.getdata('%s_common_name' % ch),settings.getdata('%s_mmr_enabled' % ch)) for ch in settings.getdata('dota_enabled_channels')}

def setup(bot):
    return

def alert(event):
    if event.channel in enabled_channels:
        t1 = time.time()
        r = latestBlurb(event.channel)
        
        if r is not None:
            t2 = time.time()
            print "[Dota] Blurb time: %4.4fms" % ((t2-t1)*1000)

            event.bot.botsay(r)



def latestBlurb(channel):
    if checktimeout(channel):
        dotaid = settings.getdata('%s_dota_id' % channel)
        if dotaid is None:
            print "[Dota] No ID on record for %s.  I should probably sort this out." % channel
            return

        settings.setdata('%s_last_match_fetch' % channel, time.time(), announce=False)

        try:
            latestmatch = steamapi.getlastdotamatch(dotaid)
        except Exception as e:
            print "[Dota] API error:", e
            return


        previousmatch = settings.trygetset('%s_last_match' % channel, latestmatch)

        if previousmatch['match_id'] != latestmatch['match_id']:
            update_channels()

            #TODO: Somewhere in here is where I do the logic to check if we've skipped a game or not

            print "[Dota] Match ID change found (%s:%s) (Lobby type %s)" % (previousmatch['match_id'], latestmatch['match_id'], str(latestmatch['lobby_type']))
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

    matchoutput = "%s has %s a game.  http://www.dotabuff.com/matches/%s " % (
        enabled_channels[channel][0], 'won' if d_victory == 'Victory' else 'lost',  latestmatch['match_id'])

    extramatchdata = "| Level {} {} {} - KDA: {}/{}/{} - CS: {}/{} - GPM: {} - XPM: {}".format(
        d_level, d_team, d_hero, d_kills, d_deaths, d_assists, d_lasthits, d_denies, d_gpm, d_xpm)

    finaloutput = matchoutput + (getMMRData(channel, dotaid) if getmmr else '') + extramatchdata

    print "[Dota] Blurb output: " + finaloutput
    return finaloutput

    #if getmmr:
    #    mmrstring = getMMRData(channel, dotaid)
    #    print "[Dota] Blurb output: " + matchoutput + mmrstring + extramatchdata
    #    return matchoutput + mmrstring + extramatchdata
    #else:
    #    print "[Dota] Blurb output: " + matchoutput + extramatchdata
    #    return matchoutput + extramatchdata


def getMMRData(channel, dotaid):
    outputstring = "Updated MMR: Solo: %s | Party: %s "

    print "[MMR] Updating mmr"

    with open('/var/www/twitch/%s/data' % channel, 'r') as d:
        olddotadata = json.loads(d.readline())

    # os.system('cd modules/node; nodejs mmr.js %s %s' % (channel, dotaid))
    wentok = updateMMR(channel)
    if not wentok:
        print "[MMR] SOMETHING MAY HAVE GONE HORRIBLY WRONG GETTING MMR"

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


def getUserDotaData(channel, datapath = '/var/www/twitch/%s/data'):
    with open(datapath % channel, 'r') as d:
        return json.loads(d.readline())


def updateMMR(channel):
    try:
        dotaid = str(settings.getdata('%s_dota_id' % channel))
    except:
        raise TypeError("No id on record")

    return node.updateMMR(channel, dotaid)


def determineSteamid(steamthing):
    # print '[Dota] Determining steamid for input: %s' % steamthing

    if steamthing.startswith('STEAM_'):
        sx,sy,sz = steamthing.split('_')[1].split(':')
        maybesteamid = (int(sz)*2+int(sy)) + STEAM_TO_DOTA_CONSTANT

    elif'steamcommunity.com/profiles/' in steamthing:
        maybesteamid = [x for x in steamthing.split('/') if x][-1] # oh I hope this works

    elif 'steamcommunity.com/id/' in steamthing:
        try:
            result = steamapi.ResolveVanityURL([x for x in steamthing.split('/') if x][-1])['response']
        except:
            return False

        if result['success'] == 1:
            maybesteamid = result['steamid']
        else:
            maybesteamid = None
    else:
        import re
        match = re.match('^\d*$', steamthing)
        if match:
            if long(match.string) < STEAM_TO_DOTA_CONSTANT:
                maybesteamid  = long(match) + STEAM_TO_DOTA_CONSTANT
            else:
                maybesteamid = match.string
        else:
            try:
                result = steamapi.ResolveVanityURL(steamthing)['response']
            except:
                return False

            if result['success'] == 1:
                maybesteamid = result['steamid']
            else:
                maybesteamid = None

    print '[Dota] Determined that steamid for %s is %s' % (steamthing, maybesteamid)
    return maybesteamid


class Lobby(object):

    GAMEMODE_All_Pick          = 1
    GAMEMODE_Captains_Mode     = 2
    GAMEMODE_Random_Draft      = 3
    GAMEMODE_Single_Draft      = 4
    GAMEMODE_All_Random        = 5
    GAMEMODE_Reverse_Captains  = 8
    GAMEMODE_Mid_Only          = 11
    GAMEMODE_Least_Played      = 12
    GAMEMODE_Limited_Heroes    = 13
    GAMEMODE_Ability_Draft     = 18
    GAMEMODE_ARDM              = 20
    GAMEMODE_1v1mid            = 21
    GAMEMODE_All_Draft         = 22

    GAMEMODES = {
        'ap': 1, 'cm':2, 'rd':3, 'sd':4, 'ar':5, 'rcm':8, 'mo': 11,
        'lp':12, 'lh':13, 'ad': 18, 'ardm':20, '1v1':21, 'rap':22 }

    SERVER_Unspecified         = 0
    SERVER_USWest              = 1
    SERVER_USEast              = 2
    SERVER_Europe              = 3
    SERVER_Korea               = 4
    SERVER_Singapore           = 5
    SERVER_Australia           = 7
    SERVER_Stockholm           = 8
    SERVER_Austria             = 9
    SERVER_Brazil              = 10
    SERVER_Southafrica         = 11
    SERVER_PerfectworldTelecom = 12
    SERVER_PerfectworldUnicom  = 13

    SERVERS = {
        'auto':0, 'uswest':1, 'useast':2, 'europe' : 3,
        'korea' : 4, 'singapore' : 5, 'australia' : 7,
        'stockholm' : 8, 'austria' : 9, 'brazil' : 10,
        'southafrica' : 11, 'perfectworldtelecom' : 12,
        'perfectworldunicom' : 13 }

    def __init__(self, channel, name=None, password=None, mode=None, region=None):
        import node

        self.channel = channel
        self.name = name
        self.password = password
        self.mode = mode
        self.region = region

        self.lobby_id = None
        self.created = False
        self.started = False

    def create(self):
        lobbyid = node.create_lobby(self.name, self.mode, self.password, self.region)

        if lobbyid is None:
            return False

        self.lobby_id = lobbyid
        self.created = True

    def leave(self):
        node.leave_lobby()

    def remake(self, name=None, password=None, mode=None, region=None):
        self.name = name or self.name
        self.password = password or self.password
        self.mode = mode or self.mode
        self.region = region or self.region

        node.leave_lobby()
        self.create()

    def start(self):
        node.start_lobby()
        self.started = True

    def shuffle(self):
        node.shuffle_lobby()

    def flip(self):
        node.flip_lobby()

    def kick_from(self, steamid): # change to accept other inputs (chat names)
        node.kick_lobby(steamid)

    def config(self): # rjackson pls
        return
