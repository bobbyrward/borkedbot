var steam = require("steam"),
    util = require("util"),
    fs = require("fs"),
    http = require('http'),
    repl = require("repl"),
    dota2 = require("dota2"),
    bot = new steam.SteamClient(),
    Dota2 = new dota2.Dota2Client(bot, true),
    zerorpc = require("zerorpc"),

    clienthellos = 0,
    clienthellolimit = 10,
    relogs = 0,
    reloglimit = 10,

    adminids = ['76561198030495011'],
    chatkeymap = {},
    pendingenables = {},

    dotauserstatus = {},
    dotauserplayingas = {},

    steam_rss_datas = [],
    dota_rss_datas = [];


/* Steam logic */
var onSteamLogOn = function onSteamLogOn(){
        util.log("Logged on.");

        bot.setPersonaState(steam.EPersonaState.Online);
        Dota2.launch();

        Dota2.on("ready", function() {
            util.log("Node-dota2 ready.");
        });

        Dota2.on("hello", function() {
            // clienthellos += 1;
            // if (clienthellos > clienthellolimit) {
            //     util.log("Too many hellos, restarting doto");
            //     Dota2.exit();
            //     Dota2.launch();
            //     clienthellos = 0;
            // }
        });

        Dota2.on("unready", function onUnready(){
            util.log("Node-dota2 unready.");
        });

        Dota2.on("chatMessage", function(channel, personaName, message) {
            util.log([channel, personaName, message].join(", "));
        });

        Dota2.on("guildInvite", function(guildId, guildName, inviter, guildInviteDataObject){
            // Dota2.setGuildAccountRole(guildId, 75028261, 3);
            util.log('Got guild invite to "' + guildName + '" by ' + inviter + ' ('+guildId+')');
        });

        Dota2.on("profileData", function(accountID, profileData) {
            util.log("Got data for " + accountID);
            // util.log(profileData);
        });

        Dota2.on("practiceLobbyCreateResponse", function(lobbyresponse, id) {
            if (id == '76561198153108180') {
                clienthellos += 1;
                if (clienthellos > clienthellolimit) {
                    util.log("Too many lobbies, restarting doto");
                    Dota2.exit();
                    Dota2.launch();
                    clienthellos = 0;
                    relogs += 1;
                    if (relogs > reloglimit) {
                        process.exit();
                    }
                }
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

        Dota2.on('error', function(err) {
            util.error("dota: Help something borked ", err);
        });

        Dota2.on("unhandled", function(kMsg) {
            util.log("UNHANDLED MESSAGE " + kMsg);
        });
    },
    onSteamSentry = function onSteamSentry(sentry) {
        util.log("Received sentry.");
        require('fs').writeFileSync('sentry', sentry);
    },
    onSteamServers = function onSteamServers(servers) {
        util.log("Received servers.");
        fs.writeFile('servers', JSON.stringify(servers));
    },
    onWebSessionID = function onWebSessionID(webSessionID) {
        util.log("Received web session id.");
        // steamTrade.sessionID = webSessionID;
        bot.webLogOn(function onWebLogonSetTradeCookies(cookies) {
            util.log("Received cookies.");
            for (var i = 0; i < cookies.length; i++) {
                // steamTrade.setCookie(cookies[i]);
            }
        });
    },
    onMessage = function onMessage(source, message, type, chatter) {
        // respond to both chat room and private messages
        util.log('Received message');

        var chattypes = {};
        for (var key in steam.EChatEntryType){
            chattypes[steam.EChatEntryType[key]] = key;
        }
        console.log(">" + source + " : " + message + " : " + chattypes[type] + " : " + chatter);

        lmessage = message.toLowerCase();

        // move over to switch eventually
        if (lmessage == 'test') {
            bot.sendMessage(source, 'Yes hello this is test');
        }

        if (lmessage == 'help') {
            bot.sendMessage(source, 'I\'m working on it!');
        }

        if (lmessage.indexOf('link twitch') > -1) {}


        if (lmessage.indexOf('enable mmr') > -1) {
            if (lmessage.split(' ')[2] == undefined) {
                bot.sendMessage(source, 'You need to give me your twitch channel (enable mmr your_twitch_channel)');
                return;
            }

            randomkey = (Math.random()+Math.random()).toString(36).substr(2,6);
            chatkeymap[lmessage.split(' ')[2]] = [randomkey, source];

            bot.sendMessage(source, "Verification key generated for twitch channel \"" + lmessage.split(' ')[2] + "\".  "
                + "Please use the following command in your chat to complete the verification: !mmrsetup verify " + randomkey);
        }

        if (adminids.indexOf(source) > -1) {
            // Commands
            if (lmessage.indexOf('verify dump') > -1) {
                bot.sendMessage(source, JSON.stringify(chatkeymap));
            }
        }
    },
    onFriend = function onFriend(steamID, relation) {
        util.log(steamID + ':' + relation);
        if (relation == steam.EFriendRelationship.PendingInvitee){
            util.log("Got friend request from " + steamID);
            bot.addFriend(steamID);

            if (steamID in pendingenables) {
                bot.sendMessage(steamID, "Twitch user " + pendingenables[steamID] + " has requested to enable mmr data features for this account.  " +
                    "If you have received this message in error, or have no idea what this is, simply ignore this message or block this bot.");

                bot.sendMessage(steamID, "To generate a verification code, please type this: enable mmr your_twitch_channel");
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

        // util.log('Dota status: ' + steamid + ' - ' + userstatusstring + ' - ' + JSON.stringify(otherargs));
        if (userstate !== '#DOTA_RP_PLAYING_AS') {
            util.log('Dota status: ' + steamid + ' - ' + userstatusstring);
            delete dotauserplayingas[steamid];
        } else {
            dotauserplayingas[steamid] = [heroname.replace('#',''), herolevel];
        }

        dotauserstatus[steamid] = userstate;

    },
    onSteamError = function onSteamError(err) {
        util.error("steam: Help something borked ", err);
        if (err.eresult == 34) {
            util.log("we got logged out");
            Dota2.exit();
        };
    },
    onSteamLogoff = function onSteamLogoff() {
        util.log("steam is derp and logged off");
        console.log(arguments);
        Dota2.exit();
        relogs = 0;

        setTimeout(bot.logOn(logOnDetails), 5000);
    };


global.config = require("./config");

// Login, only passing authCode if it exists
var logOnDetails = {
    "accountName": config.steam_user,
    "password": config.steam_pass,
};

if (config.steam_guard_code) logOnDetails.authCode = config.steam_guard_code;

var sentry = fs.readFileSync('sentry');
if (sentry.length) logOnDetails.shaSentryfile = sentry;

bot.logOn(logOnDetails);
bot.on("loggedOn", onSteamLogOn)
    .on('loggedOff', onSteamLogoff)
    .on('sentry', onSteamSentry)
    .on('servers', onSteamServers)
    .on('webSessionID', onWebSessionID)
    .on('message', onMessage)
    .on('richPresence', onRichPresence)
    .on('friend', onFriend)
    .on('error', onSteamError);

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
        reply(null, [bot.loggedOn, Dota2._gcReady]);
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
        Dota2.matchmakingStatsRequest();

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

        Dota2.matchDetailsRequest(matchid, function(err, response){
            if (err){
                console.log(err);
                reply("You probably ran out of requests, see console.")
                return;
            }
            util.log("Got data for match " + matchid);
            reply(null, response);
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

    updatemmr: function(channel, dotaid, reply) {
        reply = arguments[arguments.length - 1];

        channel = typeof channel !== 'function' ? channel : null;
        dotaid = typeof dotaid !== 'function' ? dotaid : null;

        if (!(channel && dotaid)) {
            reply("Bad arguments");
            return;
        };

        if (!Dota2._gcReady) {
            reply(null, false);
            return;
        };

        util.log("ZRPC: Updating mmr for " + channel);

        Dota2.profileRequest(dotaid, true, function(err, body){
            fs.writeFileSync(util.format('/var/www/twitch/%s/data', channel), JSON.stringify(body));
            util.log(util.format('Wrote data for %s', channel));
            reply(null, true);
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

    getsourcetvgames: function(gameoffset, h_id, reply) {
        reply = arguments[arguments.length - 1];

        gameoffset = typeof gameoffset == 'number' ? gameoffset : null;
        // h_id = typeof h_id == 'number' ? h_id : null;

        if (!Dota2._gcReady) {
            reply('GC unready');
            return;
        };

        if (typeof h_id == 'number') {
            Dota2.findSourceTVGames({start:gameoffset, heroid:h_id}, function(resp) {
                reply(null, resp);
            });
        } else {
            Dota2.findSourceTVGames({start:gameoffset}, function(resp) {
                reply(null, resp);
            });
        };
    },

    /*
        RSS stuff
    */




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

zrpcserver.on("error", function(err) {
    console.error("RPC server error: ", err);
});

zrpcserver.bind("tcp://0.0.0.0:29390");

process.on('error', function(err) {
    console.error("Help something borked: ", err);
});


//
// RSS stuff
//

var request = require('request'),
    FeedParser = require('feedparser');


function done(err) {
    if (err) {
        console.log('WE HAVE ERROR');
        // console.log(err, err.stack);
        console.log(JSON.stringify(err));
    }
}

function get_steam_news_rss(entries) {
    entries = typeof entries == 'number' ? entries : 1;

    var feedparser = new FeedParser();
    steam_rss_datas = [];

    feedparser.on('error', done);
    feedparser.on('end', done);

    feedparser.on('readable', function() {
        // console.log('ready to read');
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

    // Define our handlers
    req.on('error', done);
    req.on('response', function(res) {
        // console.log('HONK');
        if (res.statusCode != 200) return this.emit('error', new Error('Bad status code'));
        // And boom goes the dynamite
        res.pipe(feedparser);
    });
}

function get_dota_rss(entries) {
    entries = typeof entries == 'number' ? entries : 1;

    var feedparser = new FeedParser();
    dota_rss_datas = [];

    feedparser.on('error', done);
    feedparser.on('end', done);

    feedparser.on('readable', function() {
        // console.log('ready to read');
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

    // Define our handlers
    req.on('error', done);
    req.on('response', function(res) {
        // console.log('HONK');
        if (res.statusCode != 200) return this.emit('error', new Error('Bad status code'));
        // And boom goes the dynamite
        res.pipe(feedparser);
    });
}


function do_rss_updates() {
    try {
        util.log('Grabbing RSS data');
        get_steam_news_rss(10);
        get_dota_rss(10);
    } catch (ex) {
        util.log(ex);
    }
};
do_rss_updates();

var rssEvent = setInterval(do_rss_updates, 60000);
rssEvent.unref();


//
//
//

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
