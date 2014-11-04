var steam = require("steam"),
    util = require("util"),
    fs = require("fs"),
    repl = require("repl"),
    dota2 = require("dota2"),
    bot = new steam.SteamClient(),
    Dota2 = new dota2.Dota2Client(bot, true),
    zerorpc = require("zerorpc"),

    adminids = ['76561198030495011'],
    chatkeymap = {},
    pendingenables = {},

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


/* Steam logic */
var onSteamLogOn = function onSteamLogOn(){
        util.log("Logged on.");

        bot.setPersonaState(steam.EPersonaState.Online);
        Dota2.launch();

        Dota2.on("ready", function() {
            util.log("Node-dota2 ready.");
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
            if (id == '76561198153108180') return;

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
        reply("Idiot", 'something borked');
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

            for (var i = waitTimesByGroup.length - 1; i >= 0; i--) {
                mmdata[mmregions[i]] = [waitTimesByGroup[i], searchingPlayersByGroup[i]];
            };
            reply(null, mmdata);
        });
    },
    invitetomonkeysguild: function(steamid, reply) {
        reply = arguments[arguments.length - 1];

        Dota2.inviteToGuild("228630", Dota2.ToAccountID(steamid), function(err, response) {
            console.log("Guild invite callback:");
            console.log(arguments);
            reply(err, response['result']);
        });

        // reply(null);
    },
    cancelinvitetomonkeysguild: function(steamid, reply) {
        reply = arguments[arguments.length - 1];

        // Results

        // { '0': null, '1': { result: 'ERROR_NO_PERMISSION' } } -> Given when an invite has already been accepted
        // { '0': null, '1': { result: 'ERROR_ACCOUNT_ALREADY_IN_GUILD' } } -> Really now
        // { '0': null, '1': { result: 'ERROR_ACCOUNT_ALREADY_INVITED' } } -> When an invite has been sent but not accepted
        // { '0': null, '1': { result: 'SUCCESS' } } -> An invite has been rescinded


        reply();
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

        util.log("ZRPC: Updating mmr for ", channel);

        Dota2.profileRequest(dotaid, true, function(err, body){
            fs.writeFileSync(util.format('/var/www/twitch/%s/data', channel), JSON.stringify(body));
            console.log(util.format('Wrote data for %s', channel));
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

        reply(null, generatedkey == vkey);
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
    console.error("RPC server error:", err);
});

zrpcserver.bind("tcp://0.0.0.0:29390");

process.on('error', function(err) {
    console.error("Help something borked ", err);
});

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
