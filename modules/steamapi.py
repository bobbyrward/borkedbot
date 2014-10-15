import sys
sys.dont_write_bytecode = True

import requests, json

LOAD_ORDER = 90

with open('apikey', 'r') as f:
    apikey = f.readline()
del f

root = 'https://api.steampowered.com/'

# http://dev.dota2.com/showthread.php?t=58317
dotaAPIcalls = {
    "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v001/" : 
    ("hero_id","game_mode","skill","min_players","account_id","league_id","start_at_match_id","matches_requested","tournament_games_only"),
    # game_mode: see DOTA_MATCH_TYPE
    # skill: 0 for any, 1 for normal, 2 for high, 3 for very high skill (default is 0)

    "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v001/" : 
    ("match_id"),
    
    "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/v0001/" : 
    ("start_at_match_seq_num","matches_requested"),
    
    "https://api.steampowered.com/IEconDOTA2_570/GetHeroes/v0001/" : (),
    
    "https://api.steampowered.com/IDOTA2Match_570/GetLeagueListing/v0001/" : (),
    
    "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/" : (),
    
    "https://api.steampowered.com/IDOTA2Match_570/GetTeamInfoByTeamID/v001/" : 
    ("start_at_team_id","teams_requested"),
    
    "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/" : (), # ??? 
    
    "https://api.steampowered.com/IEconItems_570/GetSchema/v0001/" : (), # ???
}

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


def _apiget(path):
    return requests.get(root+path).json()

def get(path='', key=None):
    return _apiget(path) if not key else _apiget(path)[key]

def get_call(apipath, **args):
    apicall = apipath + '?key=%s' % key
    for a in args:
        apicall += '&%s=%s' % (a, args[a])
    return _apiget(apicall)

def getlastdotamatch(idnum):
    r = _apiget('IDOTA2Match_570/GetMatchHistory/V001/?key=%s&matches_requested=1&account_id=%s' % (apikey,idnum))
    try:
        r['result']['matches'][0]
    except:
        print r
    return r['result']['matches'][0]



def GetMatchHistory(
    hero_id = None, game_mode = None, skill = None, min_players = None, 
    account_id = None, league_id = None, start_at_match_id = None, 
    matches_requested = None, tournament_games_only = None):
    
    args = {k:v for k,v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v001/"
    return get_call(p, **args)

def GetMatchDetails(match_id=None):
    args = {k:v for k,v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v001/"
    return get_call(p, **args)

def GetMatchHistoryBySequenceNum(start_at_match_seq_num=None, matches_requested=None):
    args = {k:v for k,v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/v0001/"
    return get_call(p, **args)

def GetHeroes():
    p = "https://api.steampowered.com/IEconDOTA2_570/GetHeroes/v0001/"
    return get_call(p)

def GetLeagueListing():
    p = "https://api.steampowered.com/IDOTA2Match_570/GetLeagueListing/v0001/"
    return get_call(p)

def GetLiveLeagueGames():
    p = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/"
    return get_call(p)

def GetTeamInfoByTeamID(start_at_team_id = None, teams_requested = None):
    args = {k:v for k,v in locals().items() if v is not None}
    p = "https://api.steampowered.com/IDOTA2Match_570/GetTeamInfoByTeamID/v001/"
    return get_call(p, **args)

def GetPlayerSummaries():
    p = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
    return get_call(p)

def GetSchema():
    p = "https://api.steampowered.com/IEconItems_570/GetSchema/v0001/"
    return get_call(p)



def setup(bot):
    return

def alert(event):
    return