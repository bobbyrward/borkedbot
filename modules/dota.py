import sys
sys.dont_write_bytecode = True

import os
import time
import json
import requests
import steamapi
import twitchapi
import settings
import node
import timer

from secrets.moderation import USER_AGENT

from HTMLParser import HTMLParser
from twisted.internet import reactor


LOAD_ORDER = 35


POSITION_COLORS = ['Blue', 'Teal', 'Purple', 'Yellow', 'Orange',      'Pink', 'Gray', 'Light Blue', 'Green', 'Brown']

herodata = None

####
# This line evidently gives people problems when they try to run the bot when the dota_enabled_channels key isnt set
# For now, to fix this, run in an interpreter:
#
# import settings; settings.setdata('dota_enabled_channels', [])
#
# This will give it an empty list so it doesn't complain about not having the key
# I'll add an argument to settings.getdata to not raise an exception when there's no key ~eventually~

enabled_channels = {ch:(settings.getdata('%s_common_name' % ch),settings.getdata('%s_mmr_enabled' % ch)) for ch in settings.getdata('dota_enabled_channels')}

####

class ID(object):
    STEAM_TO_DOTA_CONSTANT = 76561197960265728

    def __init__(self, ID_=None, channel=None):
        ID_ = int(ID_)
        if ID_:
            if ID_ > self.STEAM_TO_DOTA_CONSTANT:
                self.steamid = ID_
                self.dotaid = self.steam_to_dota(self.steamid)
            elif ID_ < self.STEAM_TO_DOTA_CONSTANT:
                self.dotaid = ID_
                self.steamid = self.dota_to_steam(self.dotaid)
            else:
                raise ValueError()

        elif channel:
            self.dotaid = settings.getdata('%s_dota_id' % channel, coerceto=int)
            self.steamid = self.dota_to_steam(self.dotaid)

    def __cmp__(self, other):
        if isinstance(other, self.__class__):
            return self.dotaid - other.dotaid
        else:
            return self.dotaid - self.__class__(other).dotaid

    def __repr__(self):
        return "<ID - Steam: %s, Dota: %s)>" % (self.steamid, self.dotaid)

    @classmethod
    def steam_to_dota(cl, ID_):
        return int(ID_) - cl.STEAM_TO_DOTA_CONSTANT

    @classmethod
    def dota_to_steam(cl, ID_):
        return int(ID_) + cl.STEAM_TO_DOTA_CONSTANT

####

def get_enabled_channels():
    return {ch:(settings.getdata('%s_common_name' % ch),settings.getdata('%s_mmr_enabled' % ch)) for ch in settings.getdata('dota_enabled_channels')}

def update_channels():
    global enabled_channels
    enabled_channels = {ch:(settings.getdata('%s_common_name' % ch),settings.getdata('%s_mmr_enabled' % ch)) for ch in settings.getdata('dota_enabled_channels')}

def enable_channel(channel, dotaid, mmr=True, returntrueifnotnotable=False):
    en_chans = settings.getdata('dota_enabled_channels')

    settings.setdata('dota_enabled_channels', list(set(en_chans + [channel])))
    settings.trygetset('%s_common_name' % channel, channel)
    settings.setdata('%s_mmr_enabled' % channel, mmr)
    settings.setdata('%s_dota_id' % channel, dotaid)

    update_channels()
    if returntrueifnotnotable:
        if dotaid not in settings.getdata('dota_notable_players'):
            return True

def disable_channel(channel, mmr=False):
    en_chans = settings.getdata('dota_enabled_channels')
    settings.setdata('dota_enabled_channels', list(set(en_chans) - set([channel])))
    settings.setdata('%s_mmr_enabled' % channel, mmr)
    update_channels()

def getHeroes():
    global herodata
    if not herodata:
        herodata = steamapi.GetHeroes()
    return herodata

def getHeroIddict(localname=True):
    return {str(h['localized_name' if localname else 'name']):h['id'] for h in getHeroes()['result']['heroes']}

def getHeroNamedict(localname=True):
    return {h['id']:str(h['localized_name' if localname else 'name']) for h in getHeroes()['result']['heroes']}

def determineSteamid(steamthing):
    steamthing = str(steamthing)

    if steamthing.startswith('STEAM_'):
        sx,sy,sz = steamthing.split('_')[1].split(':')
        maybesteamid = (int(sz)*2+int(sy)) + ID.STEAM_TO_DOTA_CONSTANT

    elif 'steamcommunity.com/profiles/' in steamthing:
        maybesteamid = [x for x in steamthing.split('/') if x][-1]

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
        match = re.match(r'^\d*$', steamthing)
        if match:
            return ID(match.string).steamid
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
    return int(maybesteamid)


def setup(bot):
    settings.setdata('%s_matchblurb_running' % bot.chan(), False, announce=False)
    # rework into a context manager

def alert(event):
    if event.channel in get_enabled_channels():
        # msgtimer = timer.Timer('Dota message Timer')
        # msgtimer.start()
        if event.etype == 'msg': # Meh
            mes_count = settings.trygetset('%s_notable_message_count' % event.channel, 1)
            settings.setdata('%s_notable_message_count' % event.channel, mes_count + 1, announce=False)

            try:
                if not settings.trygetset('%s_matchblurb_running' % event.channel, False):
                    settings.setdata('%s_matchblurb_running' % event.channel, True, announce=False)
                    blurb(event.channel, event.bot)
                else:
                    raise RuntimeWarning('Blurb already running')
            except RuntimeWarning as e:
                pass
            except Exception as e:
               print '[Dota-Error] Match blurb failure: %s' % e
            else:
                settings.setdata('%s_matchblurb_running' % event.channel, False, announce=False)

            # msgtimer.stop()
            # print '[Dota] Matchblurb completed in %4.4f seconds.' % msgtimer.runtime()

        if event.etype == 'timer':
            try:
                rss_update = check_for_steam_dota_rss_update(event.channel)
                if rss_update:
                    print '[Dota] RSS update found: ' + rss_update
                    event.bot.botsay(rss_update)
            except Exception, e:
                print '[Dota-Error] RSS check failure: %s (%s)' % (e,type(e))


            # I'll leave this disabled until richpresence/persona stuff is fixed
            # try:
                # nblurb = notablePlayerBlurb(event.channel)
                # if nblurb:
                    # event.bot.botsay(nblurb)
            # except Exception, e:
                # print '[Dota-Error] Notable player blurb failure: %s' % e


def blurb(channel, bot, override=False):
    t1 = time.time()
    r = latestBlurb(channel, override)

    if r is not None:
        t2 = time.time()
        print "[Dota] Blurb time: %4.4fms (posting in 6 seconds)" % ((t2-t1)*1000)

        settings.setdata('%s_matchblurb_running' % channel, False, announce=False)
        reactor.callLater(6.0, bot.botsay, r)

    return r is not None

def latestBlurb(channel, override=False):
    if checktimeout(channel) or override:
        dotaid = settings.getdata('%s_dota_id' % channel)
        if dotaid is None:
            print "[Dota] No ID on record for %s.  I should probably sort this out." % channel
            return

        try:
            matches = steamapi.GetMatchHistory(account_id=dotaid, matches_requested=25)['result']['matches']
        except Exception as e:
            print 'Error with steam api data:', e
            raise e
            return

        settings.setdata('%s_last_match_fetch' % channel, time.time(), announce=False)

        latestmatch = matches[0]
        previousnewmatch = matches[1]
        previoussavedmatch = settings.trygetset('%s_last_match' % channel, latestmatch)

        if previoussavedmatch['match_id'] != latestmatch['match_id'] or override:
            if previoussavedmatch['match_id'] != previousnewmatch['match_id']:
                # Other matches have happened.

                matchlist = [m['match_id'] for m in matches]

                # If there was a problem here it either was never a problem or doesn't exist now?

                try:
                    skippedmatches = matchlist.index(previoussavedmatch['match_id']) - 1
                except:
                    skippedmatches = 0
                print '[Dota] Skipped %s matches MAYBE PROBABLY I HOPE SO' % skippedmatches
            else:
                skippedmatches = 0

            update_channels()
            notable_check_timeout = settings.trygetset('%s_notable_check_timeout' % channel, 900.0)

            settings.setdata('%s_notable_last_check' % channel, time.time() - notable_check_timeout + 60.0, announce=False)
            settings.setdata('%s_notable_message_count' % channel, settings.trygetset('%s_notable_message_limit' % channel, 50), announce=False)

            print "[Dota] Match ID change found (%s:%s) (Lobby type %s)" % (previoussavedmatch['match_id'], latestmatch['match_id'], str(latestmatch['lobby_type']))
            return getLatestGameBlurb(channel, dotaid, latestmatch, skippedmatches=skippedmatches, getmmr = get_enabled_channels()[channel][1] and str(latestmatch['lobby_type']) == '7')


def checktimeout(channel):
    twitchchecktimeout = settings.trygetset('%s_twitch_online_check_timeout' % channel, 15)
    lastonlinecheck = settings.trygetset('%s_twitch_online_last_check' % channel, time.time())
    laststreamingstate = settings.trygetset('%s_last_twitch_streaming_state' % channel, False)

    try:
        if time.time() - int(lastonlinecheck) > twitchchecktimeout:
            is_streaming = twitchapi.is_streaming(channel)
            settings.setdata('%s_last_twitch_streaming_state' % channel, is_streaming, announce=False)
        else:
            return laststreamingstate
    except Exception as e:
        print '[Dota] twitch api check error: ',e
        return False

    if is_streaming:
        if time.time() - int(twitchchecktimeout) > float(lastonlinecheck):
            settings.setdata('%s_twitch_online_last_check' % channel, time.time(), announce=False)
        else:
            return True
    else:
        return False

    laststreamcheck = settings.trygetset('%s_last_is_streaming_check' % channel, time.time())
    streamchecktimeout = settings.trygetset('%s_is_streaming_timeout' % channel, 30)

    if time.time() - int(streamchecktimeout) > float(laststreamcheck):
        getmatchtimeout = settings.trygetset('%s_get_online_match_timeout' % channel, 20)
        settings.setdata('%s_last_is_streaming_check' % channel, time.time(), announce=False)

    getmatchtimeout = settings.trygetset('%s_get_match_timeout' % channel, 30)
    lastmatchfetch = settings.trygetset('%s_last_match_fetch' % channel, time.time())

    return time.time() - int(getmatchtimeout) > float(lastmatchfetch)


def getLatestGameBlurb(channel, dotaid, latestmatch=None, skippedmatches=0, getmmr=False, notableplayers=True, splitlongnotable=True):
    if latestmatch is None:
        latestmatch = steamapi.getlastdotamatch(dotaid)

    settings.setdata('%s_last_match' % channel, latestmatch, announce=False)

    herodata = getHeroes()
    matchdata = steamapi.GetMatchDetails(latestmatch['match_id'])

    try:
        matchdata['result']['players']
    except Exception as e:
        print 'Error with match data:', e
        raise e

    playerdata = None
    for p in matchdata['result']['players']:
        if ID(p['account_id']) == ID(dotaid):
            playerdata = p
            break

    notableplayerdata = None
    separate_notable_message = False

    if notableplayers:
        notable_players = settings.getdata('dota_notable_players')
        notable_players_found = []

        if dotaid in notable_players:
            notable_players.pop(dotaid)

        for p in matchdata['result']['players']:
            if p['account_id'] in notable_players:
                playerhero = str([h['localized_name'] for h in herodata['result']['heroes'] if str(h['id']) == str(p['hero_id'])][0]) # p['heroId'] ?

                if ID(p['account_id']) != ID(dotaid):
                    notable_players_found.append((notable_players[p['account_id']], playerhero))

        if notable_players_found:
            separate_notable_message = len(notable_players_found) > 3

            notableplayerdata = "Notable players: %s" % ', '.join(['%s - %s' % (p,h) for p,h in notable_players_found])
            print "[Dota-Notable] notable player data: " + notableplayerdata
        else:
            print '[Dota-Notable] No notable players found'

    try:
        d_hero = [h['localized_name'] for h in herodata['result']['heroes'] if str(h['id']) == str(playerdata['hero_id'])][0]
    except:
        d_hero = 'Unknown Hero'

    d_team = 'Radiant' if int(playerdata['player_slot']) < 128 else 'Dire'
    d_level = playerdata['level']

    d_kills = playerdata['kills']
    d_deaths = playerdata['deaths']
    d_assists = playerdata['assists']

    d_lasthits = playerdata['last_hits']
    d_denies = playerdata['denies']

    d_gpm = playerdata['gold_per_min']
    d_xpm = playerdata['xp_per_min']

    d_victory = matchdata['result']['radiant_win'] ^ (d_team != 'Radiant')

    print "[Dota] Skipped %s matches" % skippedmatches

    if skippedmatches == -1:
        matchskipstr = '(Previous match) '
    elif skippedmatches < -1:
        matchskipstr = '(%s games ago) ' % (skippedmatches * -1)
    elif skippedmatches > 1:
        matchskipstr = '(%s skipped) ' % skippedmatches
    else:
        matchskipstr = ''

    if playerdata['leaver_status'] in [2, 3]:
        winstatus = 'abandoned'
    elif playerdata['leaver_status'] == 4:
        winstatus = 'afk abandoned'
    elif playerdata['leaver_status'] in [5, 6]:
        winstatus = 'failed to connect to'
    elif d_victory:
        winstatus = 'won'
    else:
        winstatus = 'lost'

    matchoutput = "%s%s has %s a game.  http://www.dotabuff.com/matches/%s" % (
        matchskipstr,
        get_enabled_channels()[channel][0],
        winstatus,
        latestmatch['match_id'])

    extramatchdata = "Level {} {} {} - KDA: {}/{}/{} - CS: {}/{} - GPM: {} - XPM: {}".format(
        d_level, d_team, d_hero, d_kills, d_deaths, d_assists, d_lasthits, d_denies, d_gpm, d_xpm)

    finaloutput = matchoutput + ' -- ' + extramatchdata + (' -- ' + get_match_mmr_string(channel) if getmmr else '') + (' -- ' + notableplayerdata if notableplayerdata else '')

    if splitlongnotable:
        pass

    return finaloutput

def get_match_mmr_string(channel):
    oldmmr = get_mmr_for_channel(channel)
    newmmr = fetch_mmr_for_channel(channel, True)

    if not any(newmmr):
        return '[MMR Error: No data]'

    outputstring = "MMR: %s"
    solostr = 'Solo: %s'
    partystr = 'Party: %s'

    solommrupdate = all([oldmmr[0] and newmmr[0]]) and oldmmr[0] != newmmr[0]
    partymmrupdate = all([oldmmr[1] and newmmr[1]]) and oldmmr[1] != newmmr[1]

    # Maybe someday dota won't be awful and will update profile card mmr at the end of a match

    # if solommrupdate:
        # solodiff = newmmr[0] - oldmmr[0]
        # if solodiff >= 0:
            # solodiff = '+' + str(solodiff)
        # solostr += ' (%s)' % solodiff

    solostr = solostr % newmmr[0]

    # if partymmrupdate:
        # partydiff = newmmr[1] - oldmmr[1]
        # if partydiff >= 0:
            # partydiff = '+' + str(partydiff)
        # partystr += ' (%s)' % partydiff

    partystr = partystr % newmmr[1]

    if all(newmmr):
        return outputstring % (solostr + ' | ' + partystr)
    elif newmmr[0]:
        return outputstring % solostr
    elif newmmr[1]:
        return outputstring % partystr
    else:
        return ''


def fetch_mmr_for_channel(channel, save=False):
    data = fetch_mmr_for_dotaid(settings.getdata('%s_dota_id' % channel))
    if save:
        settings.setdata('%s_last_mmr' % channel, data)
    return data

def fetch_mmr_for_dotaid(dotaid):
    return tuple(node.get_mmr_for_dotaid(dotaid))

def get_mmr_for_channel(channel):
    try:
        return settings.getdata('%s_last_mmr' % channel)
    except:
        return (None, None)


def getSourceTVLiveGameForPlayer(targetdotaid, heroid=None):
    pages = node.get_source_tv_games(heroid=heroid, pages=10)

    for page in pages:
        for game in page['game_list']:
            for player in game['players']:
                if long(player['account_id']) == long(targetdotaid):
                    return game


def searchForNotablePlayers(targetdotaid, pages=10, heroid=None, includemmr=False):
    t0 = time.time()
    herodata = getHeroes()
    notable_players = settings.getdata('dota_notable_players')

    if heroid:
        if pages > 10: pages = 10

        print '[Dota-Notable] Searching using heroid %s' % heroid

    game = getSourceTVLiveGameForPlayer(targetdotaid, heroid)

    if not game:
        return (None, None)

    players = game['players']
    notable_players_found = []
    target_found = False

    for player in players:
        if player['account_id'] in notable_players:
            # print '[Dota-Notable] %s (%s)' % ('', notable_players[player['account_id']])

            try:
                playerhero = str([h['localized_name'] for h in herodata['result']['heroes'] if str(h['id']) == str(player['hero_id'])][0])
            except:
                playerhero = POSITION_COLORS[players.index(player)]

            if ID(player['account_id']) != ID(targetdotaid):
                notable_players_found.append((notable_players[player['account_id']], playerhero))

        if ID(player['account_id']) == ID(targetdotaid):
            # print '[Dota-Notable] found target player'
            target_found = True

    #TODO: ADD THE OTHER DATA IN HERE SOMEWHERE

    if target_found:
        if notable_players_found:
            print '[Dota-Notable] Found: %s' % notable_players_found
        else:
            print '[Dota-Notable] No notable players.'

        if includemmr:
            return (notable_players_found, game['average_mmr'])
        else:
            return notable_players_found
    else:
        return (None, None) if includemmr else None


def getNotableCheckReady(channel):
    lastcheck = settings.trygetset('%s_notable_last_check' % channel, time.time())
    message_limit = settings.trygetset('%s_notable_message_limit' % channel, 50)
    notable_check_timeout = settings.trygetset('%s_notable_check_timeout' % channel, 900.0)

    if time.time() - lastcheck > notable_check_timeout:
        mes_count = settings.trygetset('%s_notable_message_count' % channel, 1)
        if mes_count <= message_limit:
            return False
        settings.setdata('%s_notable_last_check' % channel, time.time(), announce=False)
        return True
    else:
        # print notable_check_timeout - (time.time() - lastcheck)
        return False

# TODO:
#    Stop further searches if no players are found
#    Store results for use in end game blurb
#    Fine tune usage frequency
def notablePlayerBlurb(channel, pages=33):
    playerid = settings.getdata('%s_dota_id' % channel)
    userstatus = node.get_user_status(ID(playerid).steamid)
    if userstatus:
        # print 'Dota status for %s: %s' % (channel, userstatus)

        if userstatus in ["#DOTA_RP_HERO_SELECTION", "#DOTA_RP_PRE_GAME", "#DOTA_RP_GAME_IN_PROGRESS", "#DOTA_RP_PLAYING_AS"]:
            if getNotableCheckReady(channel):
                if twitchapi.is_streaming(channel):
                    if userstatus == '#DOTA_RP_PLAYING_AS':
                        playerheroid = node.get_user_playing_as(ID(playerid).steamid)
                        playerheroid = getHeroIddict(False)[playerheroid[0]]
                    else:
                        playerheroid = None

                    print "[Dota-Notable] Doing search for notable players%s" % (' using hero id' if playerheroid else '')
                    players = searchForNotablePlayers(playerid, pages, playerheroid)
                    settings.setdata('%s_notable_message_count' % channel, 0, announce=False)

                    if players:
                        return "Notable players in this game: %s" % ', '.join(['%s (%s)' % (p,h) for p,h in players])
        else:
            notable_check_timeout = settings.trygetset('%s_notable_check_timeout' % channel, 600.0)
            settings.setdata('%s_notable_last_check' % channel, time.time() - notable_check_timeout + 60.0, announce=False)


# TODO: Add additional data from new info
def get_players_in_game_for_player(dotaid, checktwitch=False, markdown=False):
    # herodata = getHeroes()
    herodict = getHeroNamedict()
    herodict[0] = "Unknown hero"

    notable_players = settings.getdata('dota_notable_players')
    game = getSourceTVLiveGameForPlayer(dotaid)

    teamformat = '%s%s \n'                   # ('## ' if markdown else '', team)
    playerformat = '%s%s: %s\n'              # ('#### ' if markdown else '  ', hero, name)
    notableformat = '%sNotable player: %s\n' # ('###### ' if markdown else '   - ', name)
    linkformat = '   - %s%s\n'               # (linktype, linkdata)

    linktypes = {
        'steam': 'http://steamcommunity.com/profiles/',
        'dotabuff': 'http://www.dotabuff.com/players/',
        'twitch': 'http://twitch.tv/'
    }

    if game:
        data = ''

        playerinfos = node.get_player_info(*[int(p['account_id']) for p in game['players']])
        noinfoids = [p['account_id'] for p in playerinfos['player_infos'] if p['name'] is None]

        playerinfodict = {pl.pop('account_id'): pl for pl in playerinfos.copy()['player_infos']}

        if noinfoids:
            noinfodatas = {int(data['friendid']): data['player_name'] for data in node.get_friend_data([ID(i).steamid for i in noinfoids])}
            for x in noinfoids:
                playerinfodict[ID(x).dotaid] = {'name': noinfodatas[ID(x).steamid]}

        for team in ['Radiant', 'Dire']:
            data += teamformat % ('## ' if markdown else '', team)

            for player in game['players'][slice(None, 5) if team=='Radiant' else slice(5, None)]:
                pname = playerinfodict[player['account_id']]['name']

                data += playerformat % ('#### ' if markdown else '  ', herodict[player['hero_id']], pname)

                if player['account_id'] in notable_players:
                    data += notableformat % ('###### ' if markdown else '   - ', notable_players[player['account_id']])

                mkupsteamlink = linkformat % (linktypes['steam'], ID(player['account_id']).steamid)
                ressteam = requests.head(linktypes['steam'] + str(ID(player['account_id']).steamid)).headers.get('location')

                if ressteam:
                    data += mkupsteamlink.replace('\n', '') + ' (%s)\n' % ressteam.split('.com')[-1][:-1]
                else:
                    data += mkupsteamlink

                data += linkformat % (linktypes['dotabuff'], player['account_id'])
                if checktwitch:
                    tname = twitchapi.get_twitch_from_steam_id(ID(player['account_id']).steamid)
                    if tname:
                        data += linkformat % (linktypes['twitch'], tname)
                data += '\n'

        return data


# TODO: Split into func that returns id:pairs and one that sets them and prints changes
def update_verified_notable_players():
    class DotabuffParser(HTMLParser):
        table_active = False
        img_section_active = False
        player_datas = list()

        def handle_starttag(self, tag, attrs):
            if tag == 'tbody':
                self.table_active = True
            if tag == 'img':
                self.img_section_active = True
            if not self.table_active: return
            if not self.img_section_active: return

            fulldatas = dict((x,y) for x,y in attrs)
            self.player_datas.append((int(fulldatas['data-tooltip-url'].split('/')[2]), fulldatas['title']))

        def handle_endtag(self, tag):
            if tag == 'tbody':
                self.table_active = False
            if tag == 'img':
                self.img_section_active = False
            if not self.table_active: return
            if not self.img_section_active: return

    parser = DotabuffParser()

    r = requests.get('http://www.dotabuff.com/players', headers={'User-agent': USER_AGENT})
    if r.status_code == 429:
        return 429

    htmldata = unicode(r.text).encode('utf8')
    parser.feed(htmldata)

    old_players = settings.getdata('dota_notable_players')
    updated_players = dict(old_players.items() + parser.player_datas)

    settings.setdata('dota_notable_players', updated_players, announce=False)

    tn = 0
    for p in dict(parser.player_datas):
        o = old_players.get(p, 'none')
        n = dict(parser.player_datas)[p]
        if o != n:
            print '[Dota-Notable] Updated player: %s -> %s' % (o, n)
            tn += 1

    return tn

def check_for_steam_dota_rss_update(channel, setkey=True):
    last_rss_check = settings.trygetset('%s_last_dota_rss_check' % channel, time.time())

    if time.time() - last_rss_check < 30.0:
        return

    settings.setdata('%s_last_dota_rss_check' % channel, time.time(), announce=False)

    rs = [li for li in node.get_steam_rss() if li]
    last_feed_url = settings.trygetset('%s_dota_last_steam_rss_update_url' % channel, '0')

    for item in rs:
        if not item: continue
        if item['author'] == 'Valve' and 'Dota 2 Update' in item['title']:
            if item['guid'] != last_feed_url:
                if last_feed_url == 'derp': last_feed_url = '0'

                try:
                    bpn_old = int([x for x in last_feed_url.split('/') if x][-1])
                    bpn_new = int([x for x in item['guid'].split('/') if x][-1])

                    if bpn_old >= bpn_new:
                        break
                except Exception as e:
                    print '[Dota-RSS] Error checking steam rss:', e
                    break

                settings.setdata('%s_dota_last_steam_rss_update_url' % channel, str(item['guid']))
                settings.setdata('%s_last_dota_rss_check' % channel, last_rss_check, announce=False)

                return str("Steam News Feed: %s - %s" % (item['title'], item['guid']))
            else:
                break


    rs = [li for li in node.get_dota_rss() if li]
    last_feed_url = settings.trygetset('%s_dota_last_dota2_rss_update_url' % channel, '0')

    for item in rs:
        if not item: continue
        if item['guid'] != last_feed_url:
            if last_feed_url == 'derp': last_feed_url = '0'

            try:
                bpn_old = int(last_feed_url.split('=')[-1])
                bpn_new = int(item['guid'].split('=')[-1])

                if bpn_old >= bpn_new:
                    break
            except Exception as e:
                print '[Dota-RSS] Error checking dota rss:', e
                break

            settings.setdata('%s_dota_last_dota2_rss_update_url' % channel, str(item['guid']))

            return str("Dota 2 Blog Post: %s - %s" % (item['title'], item['link']))
        else:
            break

def get_latest_steam_dota_rss_update():
    rs = node.get_steam_rss()

    for item in rs:
        if item['author'] == 'Valve' and 'Dota 2 Update' in item['title']:
            return str("Steam RSS News Feed: %s - %s" % (item['title'], item['guid']))


def download_all_available_replays(channel, dotaid=None, games=500):
    if not dotaid:
        dotaid = settings.getdata('%s_dota_id' % channel)

    if not os.path.isdir(node.get_replay_dir(channel)):
        os.mkdir(node.get_replay_dir(channel))

    predownloadedgames = sorted([int(f.split('.')[0]) for f in os.listdir(node.get_replay_dir(channel)) if f.endswith('.dem')])
    matchids = collect_match_ids(dotaid, games)
    gamestodownload = list(set(matchids) - set(predownloadedgames))
    gamestodownload.sort(reverse=True)

    for game in gamestodownload:
        #TODO: Add check for existing json file and check replay "freshness"

        mdetails = node.get_match_details(game)
        print 'Got %s info: %s' % (game, mdetails['match']['replayState']),

        try:
            replaysize = node.download_replay(channel, game, mdetails)
            print '- %s bytes' % replaysize
        except node.Error, e:
            print '- Ded'


def collect_match_ids(dotaid, games):
    if games > 500: raise ValueError('Cannot request more than 500 games')

    gamesdata = steamapi.GetMatchHistory(account_id=dotaid, matches_requested=games)
    matchids = sorted([m['match_id'] for m in gamesdata['result']['matches']])

    while len(matchids) != games:
        gamesdata = steamapi.GetMatchHistory(account_id=dotaid, matches_requested=games-len(matchids), start_at_match_id=matchids[0])
        matchids += [m['match_id'] for m in gamesdata['result']['matches']]
        matchids.sort(reverse=True)

    return matchids


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
