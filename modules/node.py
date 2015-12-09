import sys
sys.dont_write_bytecode = True

import re
import time
import json
import zerorpc
import settings

# DISABLE_MODULE = True
LOAD_ORDER = 36


def setup(bot):
    pass

def alert(event):
    return


class ZRPC(object):
    def __init__(self):
        self.zrpc = zerorpc.Client()

    def __enter__(self):
        self.zrpc.connect('tcp://127.0.0.1:29390')
        return self.zrpc if self.zrpc else None

    def __exit__(self, etype, evalue, tb):
        if etype is not None:
            print 'Node error:', evalue, '(%s)' % etype
        self.zrpc.close()

def get_batched_data(zfunction, ifcomp, convertjson, unpackargs, args):
    def convjson(data):
        return json.loads(data) if convertjson else data

    retries = 0
    while True:
        try:
            if ifcomp:
                return [convjson(x) for x in zfunction(*args if unpackargs else [args])]
            else:
                return [convjson(zfunction(*args if unpackargs else [args]))]
        except zerorpc.RemoteError as e:
            if e.msg == 'busy':
                time.sleep(0.2)
                retries += 1
                if retries > 25:
                    raise Exception('Took too long.')
            else:
                raise e

######################################################################

def raw_eval(raw_command):
    with ZRPC() as zrpc:
        return zrpc.evaljs(raw_command)

def restart():
    with ZRPC() as zrpc:
        return zrpc.shutdown()
    # Maybe add deferred callback for when its ready again

def status():
    with ZRPC() as zrpc:
        return zrpc.status()

def launch_dota():
    with ZRPC() as zrpc:
        return zrpc.launchdota()

def close_dota():
    with ZRPC() as zrpc:
        return zrpc.closedota()

def gc_status():
    with ZRPC() as zrpc:
        return zrpc.GCready()

def get_enum(name=None):
    with ZRPC() as zrpc:
        return zrpc.getenum(name)

def get_mm_stats():
    with ZRPC() as zrpc:
        return zrpc.getmmstats()

def get_match_details(matchid):
    with ZRPC() as zrpc:
        return zrpc.getmatchdetails(matchid)

def download_replay(channel, matchid, matchdetails):
    with ZRPC() as zrpc:
        return zrpc.downloadreplay(channel, matchid, matchdetails)

def get_replay_dir(channel):
    return '/var/www/twitch/%s/replays' % channel.lower()

########

def get_mmr_for_dotaid(dotaid):
    with ZRPC() as zrpc:
        return zrpc.getmmrfordotaid(dotaid)


def updateMMR(channel, chid, autolaunch=True):
    with ZRPC() as zrpc:
        if autolaunch:
            zrpc.launchdota()

        try:
            return zrpc.updatemmr(channel, chid)
        except Exception as e:
            print e
            return False


def verify_code(channel, code):
    with ZRPC() as zrpc:
        return zrpc.verifycheck(channel, code)

def delete_key(channel):
    with ZRPC() as zrpc:
        return zrpc.clearkey(channel)

def add_pending_mmr_enable(steamid, channel):
    with ZRPC() as zrpc:
        return zrpc.addpendingmmrenable(steamid, channel)

def remove_pending_mmr_enable(steamid):
    with ZRPC() as zrpc:
        zrpc.delpendingmmrenable(steamid)

########

def create_lobby(gameName, gameMode, password=None, serverRegion=None):
    with ZRPC() as zrpc:
        cid = settings.getdata('current_lobby_id', coerceto=str)

        if cid != '0':
            return None

        l_id = zrpc.createlobby(gameName, password, serverRegion, gameMode)
        settings.setdata('current_lobby_id', str(l_id))

        return l_id

def start_lobby():
    with ZRPC() as zrpc:
        zrpc.startlobby()

def leave_lobby():
    with ZRPC() as zrpc:
        settings.setdata('current_lobby_id', '0')
        return zrpc.leavelobby()

def get_lobby():
    with ZRPC() as zrpc:
        return settings.getdata('current_lobby_id', coerceto=str)


'''
game_name           : str, lobby title.
server_region       : int, Use the server region enum.
game_mode           : int, Use the game mode enum.
allow_cheats        : bool, allow cheats.
fill_with_bots      : bool, Fill available slots with bots?
allow_spectating    : bool, Allow spectating?
pass_key            : str, Password.
series_type         : int, Use the series type enum.
radiant_series_wins : int, Best of 3 for example, # of games won so far.
dire_series_wins    : int, Best of 3 for example, # of games won so far.
allchat             : bool, Enable all chat?
'''

def config_lobby(
    game_name = None, server_region = None, game_mode = None, allow_cheats = None,
    fill_with_bots = None, allow_spectating = None, pass_key = None, series_type = None,
    radiant_series_wins = None, dire_series_wins = None, allchat = None):
    # This doesn't work yet

    # with ZRPC() as zrpc:
    args = {k:v for k,v in locals().items() if v is not None}
    return False

def kick_lobby(userid):
    with ZRPC() as zrpc:
        return zrpc.lobby_kick(userid)

def shuffle_lobby():
    with ZRPC() as zrpc:
        return zrpc.lobby_shuffle()

def flip_lobby():
    with ZRPC() as zrpc:
        return zrpc.lobby_flip()

########

def join_chat(chatname, ctype=None):
    with ZRPC() as zrpc:
        return zrpc.joinchat(chatname, ctype)

def leave_chat(chatname):
    with ZRPC() as zrpc:
        return zrpc.leavechat(chatname)

def chat(channelname, message):
    with ZRPC() as zrpc:
        return zrpc.chat(channelname, message)

def get_chats():
    with ZRPC() as zrpc:
        return zrpc.getchats()

########

def add_friend(steamid):
    with ZRPC() as zrpc:
        return zrpc.evaljs("bot.addFriend('%s')" % steamid)

def send_steam_message(steamid, message):
    with ZRPC() as zrpc:
        return zrpc.evaljs("bot.sendMessage('%s', '%s')" % (steamid, message))

def is_friends_with(steamid):
    with ZRPC() as zrpc:
        return zrpc.evaljs('steamFriends.friends["%s"]' % steamid) is not None

class FriendDataFlags():
    Status        = 1
    PlayerName    = 2 # Default
    QueryPort     = 4
    SourceID      = 8 # Default
    Presence      = 16 # Default
    Metadata      = 32
    LastSeen      = 64
    ClanInfo      = 128
    GameExtraInfo = 256 # Default
    GameDataBlob  = 512
    ClanTag       = 1024
    Facebook      = 2048
    ALL           = 4095

def get_friend_data(steamids, datatype=None):
    steamids = [str(s) for s in steamids]
    with ZRPC() as zrpc:
        return get_batched_data(zrpc.getfrienddata, len(steamids) > 1, True, True, (steamids, datatype))

########

def invite_to_guild(guildid, steamid):
    with ZRPC() as zrpc:
        return zrpc.invitetoguild(guildid, str(steamid))

def cancel_invite_to_guild(guildid, steamid):
    with ZRPC() as zrpc:
        return zrpc.cancelinvitetoguild(guildid, str(steamid))

def set_guild_role(guildid, targetid, targetrole):
    # 0 - Kick from guild
    # 1 - Leader
    # 2 - Officer
    # 3 - Member
    with ZRPC() as zrpc:
        return zrpc.setguildrole(guildid, str(targetid), targetrole)

def kick_from_guild(guildid, targetid):
    with ZRPC() as zrpc:
        return zrpc.setguildrole(guildid, str(targetid), 0)

########

def get_source_tv_games(**gcargs):
    """
    Args:
        searchkey (str): Unknown
        leagueid (int): Blah
        heroid (int): Hero id
        startgame (int): Unknown, [0,10,20...90]
        gamelistindex (int): List version?
        lobbyids (list): Unknown

        pages (int): Alias for (startgame - 1) * 10
    """

    args = {'searchkey': '', 'leagueid': 0, 'heroid': 0, 'startgame': 0, 'gamelistindex': 0, 'lobbyids': []}

    if 'pages' in gcargs and 1 <= gcargs['pages'] <= 10:
        args['startgame'] = 10 * (gcargs['pages'] - 1)
        del gcargs['pages']

    args.update({k:gcargs[k] for k in gcargs if k in args})
    argdata = (args['searchkey'], args['leagueid'], args['heroid'], args['startgame'], args['gamelistindex'], args['lobbyids'])

    with ZRPC() as zrpc:
        return get_batched_data(zrpc.getsourcetvgames, args['startgame'] > 0, True, True, argdata)

def get_player_info(*accountids):
    with ZRPC() as zrpc:
        return json.loads(zrpc.getplayerinfo(accountids))

def get_profile_card(accountid):
    with ZRPC() as zrpc:
        return json.loads(zrpc.getprofilecard(accountid))

# def get_rich_presence_available_for_steamid(steamid):
#     with ZRPC() as zrpc:
#         return zrpc.evaljs('user_rich_presence_data.indexOf("%s") > -1' % steamid)

# def get_user_rich_presence(steamid):
#     with ZRPC() as zrpc:
#         return zrpc.evaljs('user_rich_presence_data["%s"]' % steamid)

def get_user_status(steamid):
    with ZRPC() as zrpc:
        return zrpc.evaljs("dotauserstatus['%s']" % steamid)

def get_user_playing_as(steamid):
    with ZRPC() as zrpc:
        return zrpc.evaljs("dotauserplayingas['%s']" % steamid)

def get_steam_rss(entries=0):
    with ZRPC() as zrpc:
        return zrpc.evaljs('steam_rss_datas')

    if entries:
        zrpc.evaljs('get_steam_news_rss(%s)' % int(entries))
        return zrpc.evaljs('steam_rss_datas')
    else:
        return zrpc.evaljs('steam_rss_datas')

def get_dota_rss(entries=0):
    with ZRPC() as zrpc:
        return zrpc.evaljs('dota_rss_datas')

    if entries:
        zrpc.evaljs('get_dota_news_rss(%s)' % int(entries))
        return zrpc.evaljs('dota_rss_datas')
    else:
        return zrpc.evaljs('dota_rss_datas')

def get_rich_presence(steamids):
    if isinstance(steamids, int):
        steamids = [str(steamids)]
    else:
        steamids = [str(s) for s in steamids]

    with ZRPC() as zrpc:
        data = get_batched_data(zrpc.getrichpresence, False, True, False, steamids)[0]
        intdata = {int(k):data[k] for k in data}

        for sid in intdata:
            if intdata[sid] is not None:
                for k in intdata[sid].iterkeys():
                    if k == 'party':
                        intdata[sid].update({'party': _unfuck_rp_party_data(intdata[sid]['party'])})

                    if isinstance(intdata[sid][k], basestring) and intdata[sid][k].isdigit():
                        intdata[sid].update({k: int(intdata[sid][k])})

        return intdata

def get_cached_rich_presence(steamids):
    if isinstance(steamids, int):
        steamids = [str(steamids)]
    else:
        steamids = [str(s) for s in steamids]

    with ZRPC() as zrpc:
        data = {}
        for i in steamids:
            dumbdata = zrpc.evaljs('user_rich_presence_data["%s"]' % i)
            if dumbdata and dumbdata.get('party', None):
                dumbdata.update({'party': _unfuck_rp_party_data(dumbdata['party'])})
            
            data[int(i)] = dumbdata
        
        return data

def _unfuck_rp_party_data(i):
    things = re.findall(r'(\w+?:\s\w+|members\s\{\w+?:\d*\s\})', i)
    datas = dict([x.split(': ') for x in things if not x.startswith('steam_id')])

    if 'members' in i:
        datas.update({'members': [int(x.split(': ')[1]) for x in things if x.startswith('steam_id')]})
    if 'open' in i:
        datas.update({'open': False if datas['open'] == 'false' else True})
    if 'party_id' in i:
        datas.update({'party_id': int(datas['party_id'])})

    return datas

# TODO: Test and fix lobby string unfucking
def _unfuck_rp_lobby_data(i):
    # probably can reuse the other regex
    pass
