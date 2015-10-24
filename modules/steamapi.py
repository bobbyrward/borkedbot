import sys
sys.dont_write_bytecode = True

import requests, json, traceback
from secrets.auth import STEAM_API_KEY

DISABLE_MODULE = True
LOAD_ORDER = 90

# http://dev.dota2.com/showthread.php?t=58317

root = 'https://api.steampowered.com/'

DOTA_MATCH_TYPES = {
    -1: 'Invalid',
    0: 'Public matchmaking',
    1: 'Practice',
    2: 'Tournament',
    3: 'Tutorial',
    4: 'Co-op with bots',
    5: 'Team match',
    6: 'Solo Queue',
    7: 'Ranked',
    8: 'Solo Mid 1vs1'
}


def _get_call(apipath, **args):
    apicall = apipath + '?key=%s' % STEAM_API_KEY
    raw_request=False

    for a in args:
        if a == 'raw_request':
            raw_request = args[a]
            continue

        apicall += '&%s=%s' % (a, args[a])

    requestdata = requests.get(apicall, timeout=4)

    if requestdata.status_code not in [200, 503]:
        print '[SteamAPI] API call failure:', requestdata, requestdata.reason, apipath.split('/')[-3:-2]
        try:
            requestdata.raise_for_status()
        except:
            # print traceback.format_exc()
            pass

    return requestdata.json() if not raw_request else requestdata


def getlastdotamatch(idnum):
    # r = _apiget('IDOTA2Match_570/GetMatchHistory/V001/?key=%s&matches_requested=1&account_id=%s' % (apikey,idnum)).json()
    r = GetMatchHistory(account_id=idnum, matches_requested=1)
    try:
        r['result']['matches'][0]
    except:
        print 'HELP', r
    return r['result']['matches'][0]


def GetMatchHistory(
    hero_id=None, game_mode=None, skill=None, min_players=None,
    account_id=None, league_id=None, start_at_match_id=None,
    matches_requested=None, tournament_games_only=None, raw_request=False):

    args = {k: v for k, v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v001/"

    return _get_call(p, **args)


def GetMatchDetails(match_id=None, raw_request=False):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v001/"

    return _get_call(p, **args)


def GetMatchHistoryBySequenceNum(start_at_match_seq_num=None, matches_requested=None, raw_request=False):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/v0001/"

    return _get_call(p, **args)


def GetHeroes(language='en_us', raw_request=False):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IEconDOTA2_570/GetHeroes/v0001/"

    return _get_call(p, **args)


def GetLeagueListing(raw_request=False):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetLeagueListing/v0001/"

    return _get_call(p, **args)


def GetLiveLeagueGames(raw_request=False):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/"

    return _get_call(p, **args)


def GetTeamInfoByTeamID(start_at_team_id=None, teams_requested=None, raw_request=False):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetTeamInfoByTeamID/v001/"

    return _get_call(p, **args)


def GetSchema(raw_request=False):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IEconItems_570/GetSchema/v0001/"

    return _get_call(p, **args)


def ResolveVanityURL(vanityurl, raw_request=False):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"

    return _get_call(p, **args)


def GetPlayerSummaries(steamids, raw_request=False):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"

    return _get_call(p, **args)


def GetTournamentPrizePool(leagueid=None):
    args = {k: v for k, v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IEconDOTA2_570/GetTournamentPrizePool/v1/"

    return _get_call(p, **args)


def setup(bot):
    return

def alert(event):
    return