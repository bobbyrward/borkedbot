import sys
sys.dont_write_bytecode = True

import requests, json, settings

LOAD_ORDER = 90

with open('apikey', 'r') as f:
    apikey = f.readline()

root = 'https://api.steampowered.com/'

# http://dev.dota2.com/showthread.php?t=58317
dotaAPIcalls = {
    "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v001/" : 
    ("hero_id","game_mode","skill","min_players","account_id","league_id","start_at_match_id","matches_requested","tournament_games_only"),
    # game_mode: see DOTA_MATCH_TYPE
    # skill: 0 for any, 1 for normal, 2 for high, 3 for very high skill (default is 0)

    "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v001/" : ("match_id"),
    
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

def getlastdotamatch(idnum):
    return _apiget('IDOTA2Match_570/GetMatchHistory/V001/?key=%s&matches_requested=1&account_id=%s' % (apikey,idnum))['result']['matches'][0]

def setup(bot):
    return

def alert(event):
    return