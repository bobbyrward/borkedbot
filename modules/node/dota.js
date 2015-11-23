var steam = require("steam"),
    util = require("util"),
    fs = require("fs"),
    crypto = require("crypto"),
    dota2 = require("dota2"),

    zerorpc = require("zerorpc"),
    request = require('request'),
    FeedParser = require('feedparser'),

    steamClient = new steam.SteamClient(),
    steamUser = new steam.SteamUser(steamClient),
    steamFriends = new steam.SteamFriends(steamClient),
    Dota2 = new dota2.Dota2Client(steamClient, true),

    adminids = ['76561198030495011'],
    chatkeymap = {},
    pendingenables = {},

    dotauserstatus = {},
    dotauserplayingas = {},

    steam_rss_datas = [],
    dota_rss_datas = [],

    zrpc_sourcetvgames_request_locked = false,
    zrpc_frienddata_request_locked = false;


// Load config
global.config = require("./config");

/* Steam logic */
var onSteamLogOn = function onSteamLogOn(logonResp) {
        if (logonResp.eresult == steam.EResult.OK) {
            steamFriends.setPersonaState(steam.EPersonaState.Busy); // to display your steamClient's status as "Online"
            steamFriends.setPersonaName("Borkedbot"); // to change its nickname
            util.log("Logged on.");
            Dota2.launch();
            Dota2.on("ready", function() {
                console.log("Node-dota2 ready.");
            });
            Dota2.on("unready", function onUnready() {
                console.log("Node-dota2 unready.");
            });

            Dota2.on("chatMessage", function(channel, personaName, message) {
                util.log([channel, personaName, message].join(", "));
            });

            Dota2.on("guildInviteData", function(guildId, guildName, inviter) {
                // Dota2.setGuildAccountRole(guildId, 75028261, 3);
                 util.log('Got guild invite to "' + guildName + '" by ' + inviter + ' ('+guildId+')');
            });

            Dota2.on("profileData", function(accountID, profileData) {
                util.log("Got data for " + accountID);
            });

            Dota2.on("profileCardData", function(accountID, profileCardData) {
                util.log("Got profile card data for " + accountID);
                // console.log(JSON.stringify(profileCardData));
            });

            Dota2.on("practiceLobbyCreateResponse", function(lobbyresponse, id) {
                if (id == '76561198153108180') {
                    // clienthellos += 1;
                    // if (clienthellos > clienthellolimit) {
                        // util.log("Too many lobbies, restarting doto");
                        // Dota2.exit();
                        // Dota2.launch();
                        // clienthellos = 0;
                        // relogs += 1;
                        // if (relogs > reloglimit) {
                            // process.exit();
                        // }
                    // }
                    return;
                };

                util.log("Lobby something'd ");
                console.log("id: ", id);
                console.log("Response: ", util.inspect(lobbyresponse));
            });

            Dota2.on("practiceLobbyJoinResponse", function(result, response){
                console.log('MAYBE THIS IS WHAT I WANT');
                // Dota2.joinChat(response.channelName, dota2.DOTAChatChannelType_t.DOTAChannelType_Lobby);
            });

            Dota2.on("matchmakingStatsData", function(waitTimesByGroup, searchingPlayersByGroup, disabledGroups, matchmakingStatsResponse){
                util.log('Got matchmaking stats');
                //util.log("Wait times:\n")
                //util.log(waitTimesByGroup)
                //util.log("Players searching:\n")
                //util.log(searchingPlayersByGroup)
            });

            Dota2.on("newSourceTVGamesData", function(games_data){
                // console.log("Yay new source tv games data");
                // console.log(games_data);
            });

            Dota2.on("liveLeagueGamesUpdate", function (ldata) {
                console.log(arguments);
            });

            Dota2.on('error', function(err) {
                console.error("dota: Help something borked ", err);
            });

            Dota2.on("unhandled", function(kMsg) {
                util.log("UNHANDLED MESSAGE " + kMsg);
            });
        }
    },
    onSteamServers = function onSteamServers(servers) {
        util.log("Received servers.");
        fs.writeFile('servers', JSON.stringify(servers));
    },
    onSteamLogOff = function onSteamLogOff(eresult) {
        util.log("steam is derp and logged off");
        console.log(arguments);
        Dota2.exit();
        relogs = 0;

        setTimeout(steamClient.connect(), 5000);
    },
    onSteamError = function onSteamError(err) {
        console.error("steam: help something borked ", err);
        if (err.eresult == 34) {
            util.log("we got logged out");
            Dota2.exit();
        };
        setTimeout(steamClient.connect(), 5000);
    },
    onMessage = function onMessage(source, message, type, chatter) {
        // respond to both chat room and private messages
        // util.log('Received message');
        // console.log(arguments);
        return;

        var chattypes = {};
        for (var key in steam.EChatEntryType){
            chattypes[steam.EChatEntryType[key]] = key;
        }
        console.log(">" + source + " : " + message + " : " + chattypes[type] + " : " + chatter);

        lmessage = message.toLowerCase();

        // move over to switch eventually
        if (lmessage == 'test') {
            steamClient.sendMessage(source, 'Yes hello this is test');
        }

        if (lmessage == 'help') {
            steamClient.sendMessage(source, 'I\'m working on it!');
        }

        if (lmessage.indexOf('link twitch') > -1) {}


        if (lmessage.indexOf('enable mmr') > -1) {
            if (lmessage.split(' ')[2] == undefined) {
                steamClient.sendMessage(source, 'You need to give me your twitch channel (enable mmr your_twitch_channel)');
                return;
            }

            randomkey = (Math.random()+Math.random()).toString(36).substr(2,6);
            chatkeymap[lmessage.split(' ')[2]] = [randomkey, source];

            steamClient.sendMessage(source, "Verification key generated for twitch channel \"" + lmessage.split(' ')[2] + "\".  "
                + "Please use the following command in your chat to complete the verification: !mmrsetup verify " + randomkey);
        }

        if (adminids.indexOf(source) > -1) {
            // Commands
            if (lmessage.indexOf('verify dump') > -1) {
                steamClient.sendMessage(source, JSON.stringify(chatkeymap));
            }
        }
    },
    onFriend = function onFriend(steamID, relation) {
        util.log(steamID + ':' + relation);
        if (relation == steam.EFriendRelationship.PendingInvitee){
            util.log("Got friend request from " + steamID);
            steamClient.addFriend(steamID);

            if (steamID in pendingenables) {
                steamClient.sendMessage(steamID, "Twitch user " + pendingenables[steamID] + " has requested to enable mmr data features for this account.  " +
                    "If you have received this message in error, or have no idea what this is, simply ignore this message or block this bot.");

                steamClient.sendMessage(steamID, "To generate a verification code, please type this: enable mmr your_twitch_channel");
            };
        }
        // send message to verify or whatever?
    },
    onRichPresence = function onRichPresence(steamid, userstate, herolevel, heroname) {
        userstate = typeof userstate == 'string' ? userstate : '#closing';

        userstatusstring = DOTA_RP_STATUSES[userstate.slice(1)];
        otherargs = arguments;
        delete otherargs[0];
        delete otherargs[1];

        util.log('Dota status: ' + steamid + ' - ' + userstatusstring + ' - ' + JSON.stringify(otherargs));
        if (userstate !== '#DOTA_RP_PLAYING_AS') {
            util.log('Dota status: ' + steamid + ' - ' + userstatusstring);
            delete dotauserplayingas[steamid];
        } else {
            dotauserplayingas[steamid] = [heroname.replace('#','').toLowerCase(), herolevel];
        }

        dotauserstatus[steamid] = userstate;

    };

steamUser.on('updateMachineAuth', function(sentry, callback) {
        fs.writeFileSync('sentry', sentry.bytes)
        util.log("sentryfile saved");
    callback({ sha_file: crypto.createHash('sha1').update(sentry.bytes).digest() });
});


var logOnDetails = {
    "account_name": global.config.steam_user,
    "password": global.config.steam_pass,
};
// if (global.config.steam_guard_code) logOnDetails.authCode = global.config.steam_guard_code;
var sentry = fs.readFileSync('sentry');
if (sentry.length) logOnDetails.sha_sentryfile = sentry;

steamClient.connect();
steamClient.on('connected', function() { steamUser.logOn(logOnDetails); });
steamClient.on('logOnResponse', onSteamLogOn);
steamClient.on('loggedOff', onSteamLogOff);
steamClient.on('error', onSteamError);
steamClient.on('servers', onSteamServers);
steamClient.on('message', onMessage);
steamClient.on('richPresence', onRichPresence);
steamClient.on('friend', onFriend);


///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////


var zrpcserver = new zerorpc.Server({

    /*
        Testing stuff
    */

    function_prototype: function(reply) {
        reply = arguments[arguments.length - 1];
        // varname = typeof varname !== 'function' ? varname : undefined;
        reply(null);
    },
    echo: function(name, reply) {
        reply = arguments[arguments.length - 1];
        reply(null, name);
    },
    test: function(thing, reply) {
        reply = arguments[arguments.length - 1];
        // util.log(thing);
        reply("IDIOT", 'something borked');
    },
    evaljs: function(incom, reply) {
        reply = arguments[arguments.length - 1];
        reply(null, eval(incom));
    },


    /*
        General functions
    */

    status: function(reply) {
        reply = arguments[arguments.length - 1];
        reply(null, [steamClient.loggedOn, Dota2._gcReady]);
    },
    launchdota: function(reply) {
        reply = arguments[arguments.length - 1];
        if (Dota2._gcReady) {
            reply(null, false);
        } else {
            Dota2.launch();
            reply(null, true);
        };
    },
    closedota: function(reply) {
        reply = arguments[arguments.length - 1];
        Dota2.exit();
        reply(null);
    },
    GCready: function(reply) {
        reply = arguments[arguments.length - 1];
        reply(null, Dota2._gcReady)
    },
    getenum: function(ename, reply) {
        reply = arguments[arguments.length - 1];
        ename = typeof ename !== 'function' ? ename : undefined;

        if (!ename) {
            var d2keys = Object.keys(dota2);
            d2keys.splice(d2keys.indexOf('Dota2Client'));
            reply(null, d2keys);
        } else {
            reply(null, dota2[ename]);
        };
    },
    getmmstats: function(reply) {
        reply = arguments[arguments.length - 1];
        Dota2.requestMatchmakingStats();

        Dota2.once("matchmakingStatsData", function(waitTimesByGroup, searchingPlayersByGroup, disabledGroups, matchmakingStatsResponse){
            var mmdata = {};

            for (var i = searchingPlayersByGroup.length - 1; i >= 0; i--) {
                mmdata[mmregions[i]] = searchingPlayersByGroup[i];
            };
            reply(null, mmdata);
        });
    },
    getmatchdetails: function(matchid, reply) {
        reply = arguments[arguments.length - 1];
        matchid = typeof matchid !== 'function' ? matchid : undefined;

        if (matchid === undefined) {
            reply("No match id.");
        }

        if (!Dota2._gcReady) {
            reply("GC unready")
        }

        Dota2.requestMatchDetails(matchid, function(err, response){
            if (err){
                console.log(err);
                reply("You probably ran out of requests, see console.")
                return;
            }
            util.log("Got data for match " + matchid);
            reply(null, response);
        });
    },
    getplayerinfo: function(account_ids, reply) {
        reply = arguments[arguments.length - 1];
        account_ids = Array.isArray(account_ids) ? account_ids : [account_ids];

        Dota2.once('playerInfoData', function (account_id, data) {
            reply(null, JSON.stringify(data));
        });
        Dota2.requestPlayerInfo(account_ids);
    },
    getprofilecard: function(dotaid, reply) {
        reply = arguments[arguments.length - 1];
        dotaid = typeof dotaid !== 'function' ? dotaid : null;

        if (!dotaid) {
            reply("Bad arguments");
            return;
        }

        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        }

        Dota2.requestProfileCard(Number(dotaid), function(err, body){
            util.log(util.format('Got data for %s', dotaid));
            reply(null, JSON.stringify(body));
        });
    },
    downloadreplay: function(channel, matchid, matchdetails, reply) {
        reply = arguments[arguments.length - 1];
        channel = typeof channel !== 'function' ? channel : undefined;
        matchid = typeof matchid !== 'function' ? matchid : undefined;
        matchdetails = typeof matchdetails !== 'function' ? matchdetails : undefined;

        // console.log(matchdetails);

        fs.mkdir(util.format("/var/www/twitch/%s/replays/", channel), function(err){
            if (err) {
                if (err.code != 'EEXIST') console.log(err);
            }
        });

        fs.writeFile(util.format("/var/www/twitch/%s/replays/%s.json", channel, matchid), JSON.stringify(matchdetails, null, 4), function (err) {
            if (err) console.log(err);
            util.log(util.format('Wrote %s.json for %s', matchid, channel));
        });


        // http://replay<cluster>.valve.net/570/<match_id>_<replay_salt>.dem.bz2
        var replayfile = fs.createWriteStream(util.format("/var/www/twitch/%s/replays/%s.dem", channel, matchid));
        var request = http.get(util.format("http://replay%s.valve.net/570/%s_%s.dem.bz2", matchdetails['match']['cluster'], matchid, matchdetails['match']['replaySalt']), function(response) {
            if (response.statusCode == 404) {
                try {
                    reply("Replay " + matchid + " expired (404).");
                } catch (replyerror) {
                    console.log("Match reply error, you probably ran out of requests.");
                    console.log(replyerror);
                }
            } else {
                try {
                    reply(null, parseInt(response['headers']['content-length']));
                } catch (replyerror) {
                    console.log("Match reply error, you probably ran out of requests.");
                    console.log(replyerror);
                }

                util.log(util.format("Writing %s.dem, %s bytes", matchid, response['headers']['content-length']));
                response.pipe(replayfile);
                response.once('end', function(){
                    util.log('Download complete for ' + matchid);
                });
            }
        });
    },


    /*
        MMR functions
    */

    getmmrfordotaid: function(dotaid, reply) {
        reply = arguments[arguments.length - 1];
        dotaid = typeof dotaid !== 'function' ? dotaid : null;

        if (!dotaid) {
            reply("Bad arguments");
            return;
        }

        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        }

        util.log("ZRPC: Fetching mmr for " + dotaid);

        Dota2.requestProfileCard(Number(dotaid), function(err, body){
            util.log(util.format('Got data for %s', dotaid));
            var data = {};
            body.slots.forEach(function(item) {
                if (item.stat) {
                    data[item.stat.stat_id] = item.stat.stat_score;
                }
            });
            reply(null, [data[1], data[2]]);
        });
    },

    verifycheck: function(channel, vkey, reply) {
        reply = arguments[arguments.length - 1];

        channel = typeof channel !== 'function' ? channel : null;
        vkey = typeof vkey !== 'function' ? vkey : null;

        var generatedkey = chatkeymap[channel][0];
        if (generatedkey === undefined) {
            reply("Unregistered", false);
            return;
        }

        reply(null, generatedkey == vkey ? chatkeymap[channel][1] : false);
    },
    clearkey: function(keychannel, reply) {
        reply = arguments[arguments.length - 1];
        keychannel = typeof keychannel !== 'function' ? keychannel : null;

        reply(null, delete chatkeymap[keychannel]);
    },
    addpendingmmrenable: function(steamid, channel, reply) {
        reply = arguments[arguments.length - 1];
        if (steamid in pendingenables) {
            reply(null, false);
        } else {
            pendingenables[steamid] = channel;
            reply(null, true);
        }
    },
    delpendingmmrenable: function(steamid, reply) {
        reply = arguments[arguments.length - 1];
        delete pendingenables[steamid];
        reply();
    },

    /*
        Chat functions
    */

    joinchat: function(channel, type, reply) {
        reply = arguments[arguments.length - 1];
        type = typeof type !== 'function' ? type : null;
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };

        util.log("ZRPC: Joining chat " + channel);


        Dota2.joinChat(channel, type);
        reply(null, true);
    },
    leavechat: function(channel, reply) {
        reply = arguments[arguments.length - 1];
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };
        util.log("ZRPC: Leaving chat " + channel);
        Dota2.leaveChat(channel);

        for (ch in Dota2.chatChannels) {          //
            ch = Dota2.chatChannels[ch];          // cuz rjackson can't
            if (ch.channelName == channel) {      //
                Dota2.chatChannels.splice(ch);    // This is probably an awful way
                break;                            // to go about doing this but
            };                                    // I don't really know js
        };                                        //

        reply(null, true);
    },
    chat: function(channel, message, reply) {
        reply = arguments[arguments.length - 1];
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };
        util.log("ZRPC: Sending message to " + channel + ": " + message);

        Dota2.sendMessage(channel, message);

        var isok = false;
        for (ch in Dota2.chatChannels) {
            ch = Dota2.chatChannels[ch];
            if (ch.channelName == channel) {
                isok = true;
                break;
            };
        };

        reply(null, isok);
    },
    getchats: function(reply) {
        reply = arguments[arguments.length - 1];
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };
        util.log("ZRPC: Chat channels requested");
        reply(null, Dota2.chatChannels);
    },

    /*
        Lobby functions
    */

    createlobby: function(gameName, password, serverRegion, gameMode, reply) {
        reply = arguments[arguments.length - 1];

        gameName = typeof gameName !== 'function' ? gameName : undefined;
        password = typeof password !== 'function' ? password : undefined;
        serverRegion = typeof serverRegion !== 'function' ? serverRegion : undefined;
        gameMode = typeof gameMode !== 'function' ? gameMode : 1; // All pick

        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };

        util.log("ZRPC: Creating lobby");

        Dota2.leavePracticeLobby();

        if (Dota2._gcReady) {
            Dota2.createPracticeLobby(gameName, password, serverRegion, gameMode, function (err, body) {
                console.log("Lobby created? ",err); // DOTA_JOIN_RESULT_ALREADY_IN_GAME should mean OK for whatever reason
                console.log(body);
            });
            Dota2.once("practiceLobbyCreateResponse", function(lobbyresponse, id) {
                reply(null, id);
            });
        } else {
            reply(null, "GC not ready");
        };
    },
    startlobby: function(reply) {
        reply = arguments[arguments.length - 1];
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };
        Dota2.launchPracticeLobby();
        reply(null);
    },
    leavelobby: function(reply) {
        reply = arguments[arguments.length - 1];
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };
        util.log("ZRPC: Leaving lobby");

        Dota2.leavePracticeLobby();
        Dota2.once("practiceLobbyResponse", function(lobbyresponse, id) {
            if (id.result == 'DOTA_JOIN_RESULT_INVALID_LOBBY') {
                reply(null, false);

            } else if (id.result == 'DOTA_JOIN_RESULT_ALREADY_IN_GAME') {
                reply(null, true);
            } else {
                reply(null, id.result);
            };
        });
    },
    lobby_kick: function(id, reply) {
        reply = arguments[arguments.length - 1];
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };
        Dota2.practiceLobbyKick(accountid, function(blarg){
            console.log("someone was kicked from the lobby:" + arguments);
        });
        reply(null);
    },
    lobby_shuffle: function(reply) {
        reply = arguments[arguments.length - 1];
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };
        Dota2.balancedShuffleLobby();
        reply(null);
    },
    lobby_flip: function(reply) {
        reply = arguments[arguments.length - 1];
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };
        Dota2.flipLobbyTeams();
        reply(null);
    },
    lobby_config: function(id, options, reply) {
        reply = arguments[arguments.length - 1];
        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };

        Dota2.configPracticeLobby(id, options, function() {
            console.log('help what am i doing ' + arguments);
        });
        reply(null, "Ok I hoped that worked");
    },

    /*
        Guild stuff
    */

    invitetoguild: function(guildid, targetid, reply) {
        reply = arguments[arguments.length - 1];

        guildid = typeof guildid !== 'function' ? guildid : undefined;
        targetid = typeof targetid !== 'function' ? targetid : undefined;

        if (!(guildid && targetid)) {
            reply('Bad arguments');
            return;
        }

        if (!Dota2._gcReady) {
            reply('GC unready');
            return;
        };

        Dota2.inviteToGuild(guildid, Dota2.ToAccountID(targetid), function(err, response) {
            reply(err, response['result']);
        });
    },
    cancelinvitetoguild: function(guildid, targetid, reply) {
        reply = arguments[arguments.length - 1];

        guildid = typeof guildid !== 'function' ? guildid : undefined;
        targetid = typeof targetid !== 'function' ? targetid : undefined;

        if (!(guildid && targetid)) {
            reply('Bad arguments');
            return;
        }

        if (!Dota2._gcReady) {
            reply('GC unready');
            return;
        };

        Dota2.cancelInviteToGuild(guildid, Dota2.ToAccountID(targetid), function(err, response) {
            reply(err, response['result']);
        });
    },
    setguildrole: function(guildid, targetid, targetrole, reply) {
        reply = arguments[arguments.length - 1];

        guildid = typeof guildid !== 'function' ? guildid : undefined;
        targetid = typeof targetid !== 'function' ? targetid : undefined;
        targetrole = typeof targetrole !== 'function' ? targetrole : undefined;

        if (!(guildid && targetid && typeof targetrole != undefined)) {
            reply('Bad arguments');
            return;
        }

        if (!Dota2._gcReady) {
            reply('GC unready');
            return;
        };

        // 0 - Kick member from guild.
        // 1 - Leader.
        // 2 - Officer.
        // 3 - Member.

        Dota2.setGuildAccountRole(guildid, Dota2.ToAccountID(targetid), targetrole, function(err, response) {
            reply(err, response['result']);
        });
    },
    invitetomonkeysguild: function(targetid, reply) {
        reply = arguments[arguments.length - 1];

        targetid = typeof targetid !== 'function' ? targetid : undefined;

        if (!(targetid)) {
            reply('Bad arguments');
            return;
        }

        if (!Dota2._gcReady) {
            reply('GC unready');
            return;
        };

        Dota2.inviteToGuild("228630", Dota2.ToAccountID(targetid), function(err, response) {
            reply(err, response['result']);
        });
    },
    cancelinvitetomonkeysguild: function(targetid, reply) {
        reply = arguments[arguments.length - 1];

        // { result: 'ERROR_NO_PERMISSION' } -> Given when an invite has already been accepted
        // { result: 'ERROR_ACCOUNT_ALREADY_IN_GUILD' } -> Really now
        // { result: 'ERROR_ACCOUNT_ALREADY_INVITED' } -> When an invite has been sent but not accepted
        // { result: 'SUCCESS' } -> An invite has been rescinded

        targetid = typeof targetid !== 'function' ? targetid : undefined;

        if (!(targetid)) {
            reply('Bad arguments');
            return;
        }

        if (!Dota2._gcReady) {
            reply('GC unready');
            return;
        };

        Dota2.cancelInviteToGuild("228630", Dota2.ToAccountID(targetid), function(err, response) {
            reply(err, response['result']);
        });
    },

    /*
        SourceTV
    */

    getsourcetvgames: function(searchkey, leagueid, heroid, startgame, gamelistindex, lobbyids, reply) {
        reply = arguments[arguments.length - 1];

        if (zrpc_sourcetvgames_request_locked) {
            reply("busy");
            return;
        }

        searchkey = typeof searchkey == 'string' ? searchkey : '';
        leagueid = typeof leagueid == 'number' ? leagueid : 0;
        heroid = typeof heroid == 'number' ? heroid : 0;
        startgame = typeof startgame == 'number' ? startgame : 0;
        gamelistindex = typeof gamelistindex == 'number' ? gamelistindex : 0;
        lobbyids = typeof lobbyids == 'object' ? lobbyids : [];

        var totalresponses = (startgame/10) + 1,
            receivedgames = 0;

        if (lobbyids.length > 0) {
            totalresponses++;
        }

        if (!Dota2._gcReady) {
            reply('GC unready');
            return;
        };

        zrpc_sourcetvgames_request_locked = true;
        util.log("Expecting", totalresponses, "responses.");

        if (totalresponses > 1) {
            var stvdata = function(gamedata) {
                for (var i = gamedata.game_list.length - 1; i >= 0; i--) {
                    gamedata.game_list[i].lobby_id = ""+gamedata.game_list[i].lobby_id
                    gamedata.game_list[i].server_steam_id = ""+gamedata.game_list[i].server_steam_id
                }

                receivedgames++;
                // util.log("Received game", receivedgames);
                reply(null, JSON.stringify(gamedata), receivedgames < totalresponses);

                if (receivedgames == totalresponses) {
                    util.log("Received all games, removing games listener.");
                    Dota2.removeListener('newSourceTVGamesData', stvdata);
                    zrpc_sourcetvgames_request_locked = false;
                }
            };
            Dota2.on('newSourceTVGamesData', stvdata);

        } else {
            Dota2.once('newSourceTVGamesData', function(gamedata) {
                    for (var i = gamedata.game_list.length - 1; i >= 0; i--) {
                        gamedata.game_list[i].lobby_id = ""+gamedata.game_list[i].lobby_id
                        gamedata.game_list[i].server_steam_id = ""+gamedata.game_list[i].server_steam_id
                    }
                    util.log("Received game data.");
                    reply(null, JSON.stringify(gamedata));
                    zrpc_sourcetvgames_request_locked = false;
            });
        }

        Dota2.newRequestSourceTVGames({
            search_key: searchkey,
            league_id: leagueid,
            hero_id: heroid,
            start_game: startgame,
            game_list_index: gamelistindex,
            lobby_ids: lobbyids
        });
    },

    /*
        Node-steam stuff
    */

    getfrienddata: function(steamids, datatype, reply) {
        reply = arguments[arguments.length - 1];

        steamids = Array.isArray(steamids) ? steamids : [steamids];
        datatype = typeof datatype !== 'function' ? datatype : 3154;

        /*

        enum EClientPersonaStateFlag flags
        {
            Status = 1;
            PlayerName = 2; *
            QueryPort = 4;
            SourceID = 8; *
            Presence = 16; *
            Metadata = 32;
            LastSeen = 64;
            ClanInfo = 128;
            GameExtraInfo = 256; *
            GameDataBlob = 512;
            ClanTag = 1024;
            Facebook = 2048;
        };

        */

        if (zrpc_frienddata_request_locked) {
            reply("busy");
            return;
        }

        if (!steamClient.loggedOn) {
            reply("Steam not ready.");
            return;
        }

        var totalresponses = steamids.length,
            receivedresponses = 0,
            unrequestedresponses = 0;

        zrpc_frienddata_request_locked = true;

        console.log("Expecting", totalresponses, "friend datas.");
        console.log("Looking up", steamids);

        var sfonps = function(data) {
            if (steamids.indexOf(data.friendid) > -1) {
                console.log("Received friend data");
                receivedresponses++;
            } else {
                console.log("Caught unrequested friend data");
                // unrequestedresponses++;
                // if (unrequestedresponses == totalresponses) {
                    // zrpc_frienddata_request_locked = false;
                    // steamFriends.removeListener('personaState', sfonps);
                    // reply("Bad input ids, convert to strings please.");
                // };
                return;
            }

            reply(null, JSON.stringify(data), receivedresponses < totalresponses);

            if (receivedresponses == totalresponses) {
                console.log("Got all the friend datas, removing listener");
                steamFriends.removeListener('personaState', sfonps);
                zrpc_frienddata_request_locked = false;
                return;
            }
        };

        setTimeout(function() {
            if (receivedresponses != totalresponses) {
                msg = util.format("Did not receive all requested data. (%s/%s)", receivedresponses, totalresponses)

                console.log(msg);
                reply(msg);
                
                steamFriends.removeListener('personaState', sfonps);
                zrpc_frienddata_request_locked = false;
            }
        }, 10000);

        steamFriends.on('personaState', sfonps);
        steamFriends.requestFriendData(steamids, datatype);
    },

    /*
        Exiting stuff
    */

    shutdown: function(reply) {
        reply = arguments[arguments.length - 1];
        util.log("ZRPC: Terminating via zrpc/python command");

        try {
            util.log("ZRPC: Leaving lobby");
            Dota2.leavePracticeLobby();
        } catch (e) {}

        try {
            util.log("ZRPC: Exiting dota");
            Dota2.exit();
        } catch (e) {}

        try {
            util.log("ZRPC: Logging off steam");
            bot.logOff();
        } catch (e) {}

        reply(null, true);

        setTimeout(function(){
            try {
                zrpcserver.close();
            }catch (e) {}
            process.exit();
        }, 2000);
    },
    kill: function(reply) {
        reply = arguments[arguments.length - 1];
        setTimeout(function(){
            process.exit();
        }, 1000);
        reply(null, true);
    }
});



///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////


zrpcserver.on("error", function(err) {
    console.error("RPC server error: ", err);
});

zrpcserver.bind("tcp://0.0.0.0:29390");
console.log('Starting zrpc server');

process.on('error', function(err) {
    console.error("Process error: ", err);
});


function rss_error(err) {
    if (err) console.log(util.format('RSS error: %s (%s)', err.message, JSON.stringify(err)));
};

function get_steam_news_rss(entries) {
    entries = typeof entries == 'number' ? entries : 10;

    var feedparser = new FeedParser();

    feedparser.on('error', rss_error);
    feedparser.on('end', rss_error);

    feedparser.on('readable', function() {
        setTimeout(function(e){
            for (var i = 0; i < e; i++) {
                var rsss = feedparser.read();
                steam_rss_datas[i] = rsss;
            };
            while (item = feedparser.read()){}
            // feedparser.end()
        }, 500, entries);
    });

    req = request('http://store.steampowered.com/feeds/news.xml', {
        timeout: 5000,
        pool: false
    });

    req.setMaxListeners(50);

    req.on('error', rss_error);
    req.on('response', function(res) {
        if (res.statusCode != 200) return this.emit('error', new Error('Bad status code'));
        res.pipe(feedparser);
    });
};

function get_dota_rss(entries) {
    entries = typeof entries == 'number' ? entries : 10;

    var feedparser = new FeedParser();

    feedparser.on('error', rss_error);
    feedparser.on('end', rss_error);

    feedparser.on('readable', function() {
        setTimeout(function(e){
            for (var i = 0; i < e; i++) {
                var rsss = feedparser.read();
                dota_rss_datas[i] = rsss;
            };
            while (item = feedparser.read()){}
            // feedparser.end()
        }, 500, entries);
    });

    req = request('http://blog.dota2.com/feed/', {
        timeout: 5000,
        pool: false
    });

    req.setMaxListeners(50);

    req.on('error', rss_error);
    req.on('response', function(res) {
        if (res.statusCode != 200) return this.emit('error', new Error('Bad status code'));
        res.pipe(feedparser);
    });
};

function do_rss_updates() {
    try {
        // util.log('Grabbing RSS data');
        get_steam_news_rss(10);
        get_dota_rss(10);
    } catch (ex) {
        util.log(ex);
    }
};
do_rss_updates();

var rssEvent = setInterval(do_rss_updates, 20000);
rssEvent.unref();


var DOTA_RP_STATUSES = {
    "closing"                            : "Closing",
    "DOTA_RP_INIT"                       : "Main Menu",
    "DOTA_RP_IDLE"                       : "Main Menu (Idle)",
    "DOTA_RP_WAIT_FOR_PLAYERS_TO_LOAD"   : "Waiting for loaders",
    "DOTA_RP_HERO_SELECTION"             : "Hero Selection",
    "DOTA_RP_STRATEGY_TIME"              : "Strategy Time",
    "DOTA_RP_PRE_GAME"                   : "Pre Game",
    "DOTA_RP_GAME_IN_PROGRESS"           : "Playing A Game",
    "DOTA_RP_GAME_IN_PROGRESS_CUSTOM"    : "Playing %s1",
    "DOTA_RP_PLAYING_AS"                 : "as %s2 (Lvl %s1)",
    "DOTA_RP_POST_GAME"                  : "Post Game",
    "DOTA_RP_DISCONNECT"                 : "Disconnecting",
    "DOTA_RP_SPECTATING"                 : "Spectating A Game",
    "DOTA_RP_CASTING"                    : "Casting A Game",
    "DOTA_RP_WATCHING_REPLAY"            : "Watching A Replay",
    "DOTA_RP_WATCHING_TOURNAMENT"        : "Watching A Tournament Game",
    "DOTA_RP_WATCHING_TOURNAMENT_REPLAY" : "Watching A Tournament Replay",
    "DOTA_RP_FINDING_MATCH"              : "Finding A Match",
    "DOTA_RP_SPECTATING_WHILE_FINDING"   : "Finding A Match & Spectacting",
    "DOTA_RP_PENDING"                    : "Friend Request Pending",
    "DOTA_RP_ONLINE"                     : "Online",
    "DOTA_RP_BUSY"                       : "Busy",
    "DOTA_RP_AWAY"                       : "Away",
    "DOTA_RP_SNOOZE"                     : "Snooze",
    "DOTA_RP_LOOKING_TO_TRADE"           : "Looking To Trade",
    "DOTA_RP_LOOKING_TO_PLAY"            : "Looking To Play",
    "DOTA_RP_PLAYING_OTHER"              : "Playing Other Game",
    "DOTA_RP_ACCOUNT_DISABLED"           : "Matchmaking Disabled Temporarily",
    "DOTA_RichPresence_Help"             : "What's new? Set a custom status here!",
    "DOTA_RP_QUEST"                      : "On A Training Mission",
    "DOTA_RP_BOTPRACTICE"                : "Playing Against Bots",
    "DOTA_RP_TRAINING"                   : "On a Training Mission" },

    mmregions = ['USWest',
                 'USEast',
                 'Europe',
                 'Singapore',
                 'Shanghai',
                 'Brazil',
                 'Korea',
                 'Austria',
                 'Stockholm',
                 'Australia',
                 'SouthAfrica',
                 'PerfectWorldTelecom',
                 'PerfectWorldUnicom',
                 'Dubai',
                 'Chile',
                 'Peru'];


/*

Steam friend status enum:

    None              = 0;
    Blocked           = 1;
    PendingInvitee    = 2; obsolete "renamed to RequestRecipient"
    RequestRecipient  = 2;
    Friend            = 3;
    RequestInitiator  = 4;
    PendingInviter    = 4;  obsolete "renamed to RequestInitiator"
    Ignored           = 5;
    IgnoredFriend     = 6;
    SuggestedFriend   = 7;
    Max               = 8;


Dota matchmaking regions

    ['USWest',               matchgroup: 0
    'USEast',               matchgroup: 1
    'Europe',               matchgroup: 2
    'Singapore',            matchgroup: 3
    'Shanghai',             matchgroup: 4
    'Brazil',               matchgroup: 5
    'Korea',                matchgroup: 6
    'Austria',              matchgroup: 8
    'Stockholm',            matchgroup: 7
    'Australia',            matchgroup: 9
    'SouthAfrica',          matchgroup: 10
    'PerfectWorldTelecom',  matchgroup: 11
    'PerfectWorldUnicom',   matchgroup: 12
    'Dubai',                matchgroup: 13
    'Chile',                matchgroup: 14
    'Peru']                 matchgroup: 15


https://github.com/DoctorMcKay/node-steamcommunity

request.post('http://steamcommunity.com/groups/group_url/announcements', {form: {
    sessionID: g_sessionID,
    action: 'post',
    headline: 'Announcement Title',
    body: "Announcement content"
}});


*/

