# borkedbot

Custom, extensible, work in progress chatbot for twitch.

Borkedbot is a python IRC bot built for twitch.tv chats.  It interfaces with Steam and Dota 2 through node-steam and node-dota2, along with accessing the Steam and Twitch APIs.  Borkedbot currently runs on Python 2.7 in a linux environment.  No guarentees are made about stability, and some features are limited by the twitch and steam API's availablity.

## Dependencies

##### Python modules required:

  * [twisted](https://twistedmatrix.com/trac/)
  * [redis](https://github.com/andymccurdy/redis-py)
  * [requests](http://python-requests.org/)
  * [dill](http://trac.mystic.cacr.caltech.edu/project/pathos/wiki/dill)
  * [dateutil](http://labix.org/python-dateutil)

Most, if not all, of these pagkages can be installed via [pip](https://pip.pypa.io/en/latest/installing.html).

##### Other:

  * [node-steam](https://github.com/seishun/node-steam)
  * [node-dota2](https://github.com/RJacksonm1/node-dota2)
  * [Steam API access](http://steamcommunity.com/dev/apikey)
  * [Twitch API access](https://github.com/justintv/twitch-api)

For Steam (non-API) and Dota 2 related functionality a running instance of node-steam with node-dota2 is required.  See [dota.js](modules/node/dota.js) for more information.

# Features

Borkedbot is designed to be interfaced almost entirely through chat.  _Stuff and things._

Redis settings keys may be manually changed for debugging or maintence reasons, but is usually not needed.  It should be noted that keys are in python pickle format.  Importing the settings module from an interpreter is the suggested method of interaction.
<!-- Not sure about this part. -->

<!-- Blah blah something about automatic messages like the dota blurb -->

# Commands
Commands are currently created manually per channel, with some that can be used across channels.  Part of the upcomming command overhaul will be the ability to create simple commands through chat.  Complex commands will probably still need to be created manually.  The new command system may include a way to generate an information page automatically or on demand in the future.

Commands have varying levels of permissions and rules regarding when and in which channels they are active for.  They can be disabled per channel by request of the channel owner.  Commands that only work for the bot host (imayhaveborkedit) will be ommited due to irrevelance to the following section.

## Current commands
###### List is highly subject to change, see [chatrules.py](modules/chatrules.py) for the most current commited commands.

### Arguments
  * `[arg]` - Optional argument.
  * `<arg>` - Required argument.
  * `'arg'` - Literal argument.  The word in quotes _is_ the argument.  Multiple arguments without quotes are considered literals as well.
  * `arg1 | arg2` - Multiple arguments.  Either can be used, ex: `!command arg1` or `!command arg2`

### Permissions heirarchy
The permissions tree is as follows.  Highest permissions on the left, lowest on the right.

`Special` > `Broadcaster` > `Mods` > `Subscribers` > `All`

##### Special
Only the bot host (imayhaveborkedit) can use these.  Usually reserved for test commands or other convience commands.

The rest should be self explainatory.


## Global commands
These commands work in all channels by default, but may be blacklisted for certain channels.


### `!uptime [channel]`
Says how long the channel has been streaming for.  If used in a channel that is currently hosting another, the command will return the uptime for the hosted channel instead.

##### Category: `Global`
##### Permission: `All users`
##### Typical output: `{user}: {channel} has been streaming for aproximately {H} hours and {M} minutes.`
##### Cooldown: `15 seconds`
##### Arguments:
`[channel]` - Optional argument to get the uptime of another channel.

----

### `!saysomething [two word seed]`
Generates a sentence using markov chains from words collected from chat.  Use at your own risk.

##### Category: `Global`
##### Permission: `All users`
##### Typical output: `Completely random jibberish`
##### Cooldown: `30 seconds`
##### Arguments:
`[two word seed]` - Takes two words and tries to create a sentence using those to start with.  Typically inferior to using the command without the argument.

----

### `Borkedbot, ...?`
Ask borkedbot a question and his magic 8 ball will give you an answer.  Message must end with a question mark.

##### Category: `Global`
##### Permission: `All users`
##### Typical output: `Magic 8 ball responses, plus a few extra.`
##### Cooldown: `15 seconds`
##### Arguments:
`...` - Some question that you want to ask.

---

### `!source [user]`
### `!guts [user]`
Returns a link to the github page.  You probably found this page that way.
<!-- [I'm so meta, even this acronym.](http://xkcd.com/917/) -->

##### Category: `Global`
##### Permission: `Mods`
##### Typical output: `BLEUGH https://github.com/imayhaveborkedit/borkedbot`
##### Cooldown: `10 seconds`
##### Arguments:
`[user]` - Prepends the output with the supplied user instead of the one who invoked the command.

---

### `!recurring [options...]`
Creates or manages recurring events.  Recurring events are automated messages that will be said in chat at an arbritrary interval, rounded to the nearest 5 seconds.  This system is unstable, do not expect much.  It works, but just barely.  Events are not restarted after the bot restarts, and possibly if the bot is disconnected from irc and reconnects.

##### Category: `Global`
##### Permission: `Broadcaster`
<!-- ##### Typical output: `` -->
##### Cooldown: `0 seconds`
##### Arguments:
  * `[new]` - Create a new recurring event.
    - `<name>` - The name of the event.  Names may not have the character ' or spaces in them.
    - `<timeout>` - Number of seconds to wait between messages.  Rounded to the nearest five.  Must only contain numbers.
    - `<message...>` - The message to say.  The rest of the message is consumed, spaces and all.
  * `[del]` - Stop and delete a recurring event.
    - `<name>` - The name of the event.  Names can be found with the `list` option.  Only one name is consumed.
  * `[delall]` -  Stop and delete all events.
  * `[set timeout]` - Change the frequency of the event.  More options will be added in addition to `timeout`.
    - `<name>` - Name of the event.
    - `<timeout>` - Number of seconds to change the timeout to.
    - `now` - Optional flag to imediately trigger the event instead of waiting for the timeout.
  * `[start]` - Starts a stopped event.
    - `<name>` - Name of the event.
  * `[stop]` - Stops a running event.
    - `<name>` - Name of the event.
  * `[skip]` - Resets the event's timeout, effectively restarting it.
  * `[list]` - List the names of all running events.
  * `[status]` - Status information of all events (running or stopped).
    - `[name]` - Requests running status on a single event instead of all events.
  * `[dump]` - Dumps all event data to the console.  Not intended for use by anyone other than the bot host.


## Feature Specific Commands
These commands work in all channels if the channel is enabled for something, i.e. Dota related commands work in Dota related channels.


### `!mmr ['update']`
Displays the streamer's Dota 2 ranked MMR.

##### Category: `Dota`
##### Permission: `All users`
##### Typical output: `Solo: 5000 | Party: 5000`
##### Cooldown: `15 seconds`
##### Arguments:
`update` - __Mods Only__ - Requests a manual update of MMR.  Not usually needed as borkedbot should keep track of MMR already.

---

### `!dotabuff`
Returns a link to the streamer's dotabuff if Dota features are enabled.

##### Category: `Dota`
##### Permission: `All users`
##### Typical output: `{user}: http://www.dotabuff.com/players/{streamer dota id}`
##### Cooldown: `10 seconds`

---

### `!notableplayers [pages]`
Identifies notable players in the streamers current match.  Command searches through the live games data, the same data in the Dota 2 'Live Games' tab.  Notable players are defined as:

  * The dotabuff verified players list
  * Streamers who have Dota features enabled (_not yet implemented_)
  * Other streamers of note on twitch (_not yet implemented_)

Will be removed in the future in favor of an automatic system.

##### Category: `Dota, temporary`
##### Permission: `Mods`
##### Typical output: `Notable players in this game: {Player name} ({Hero in current match}), ...`
##### Cooldown: `10`
##### Arguments:
`[pages]` - Number of pages to search through.  Every page has 6 games on it.  Defaults to 8.  High level ranked matches with pro players are more likely to be at the top of the list.

---

### `!mmrsetup [help | addyou | addme <steam thing> | verify <code> ]`
Setup command to register a streamer with borkedbot and enable dota features.  The process goes as follows:

  1. Streamer types `!mmrsetup` and Borkedbot replies with instructions.
  2. Streamer types `!mmrsetup` with the `addme` or `addyou` options.
  3. Streamer somehow adds Borkedbot as a friend on steam.
  4. Borkedbot may initiate a steam chat with that person (if that feature isn't broken), otherwise the streamer says `enable mmr` in steam chat.
  5. Borkedbot generates a code for the streamer to verify with in chat.
  6. Once verified, Borkedbot congratulates you on a job well done and Dota features are enabled.

##### Category: `Dota`
##### Permission: `Broadcaster`
<!-- ##### Typical output: `Depends on argument.  Command will attempt to guide you through the setup process.` -->
##### Cooldown: `5 seconds`
##### Arguments:
  * `[help]` - Displays information about the command.
  * `[addyou]` - Returns borkedbot's steam profile link and a steam uri link for use with the `Win+R` Run dialog.
  * `[addme]` - Requests that borkedbot attempt to add the broadcaster from...
    * `<steam thing>` - A steam profile link, id, vanity name, dota id, etc.  Borkedbot's will be used as an example.  Valid options:
      * Steam Community profile link, either work:
        * `http://steamcommunity.com/profiles/76561198153108180/`
        * `http://steamcommunity.com/id/Borkedbot/`
      * Or just the end part:
        * `76561198153108180`
        * `Borkedbot`
      * Dota ID (can be found on your dota profile): `192842452`
      * The other Steam ID that looks like this: `STEAM_0:0:96421226`
  * `[verify]` - Verifies the streamer with borkedbot and enables dota related features in the channel.
    * `<code>` - Code given to the streamer by borkedbot through steam chat to verify themselves.

---

### `!dotaconfig [status | setname <name> | enable <dota | mmr> | disable <dota | mmr>]`
Configuration command for dota related settings.  More options will be added in the future.

##### Category: `Dota`
##### Permission: `Broadcaster`
<!-- ##### Typical output: `Depends on argument.  No help argument available yet, use this for reference.` -->
##### Cooldown: `5 seconds`
##### Arguments:
  * `[status]` - Currently displays if MMR features are enabled.  Will show more information in the future.
  * `[setname]` - Sets the name that will be used to refer to the streamer.
    * `<name>` -  Said name.
  * `[enable]` and `[disable]` - Enable and disable the following features:
    * `<dota>` - Dota related functions
    * `<mmr>` - MMR related functions

---

### `!lobby [options...]`
Manages a private lobby in Dota 2.  This command is part of the upcomming subgames feature.  Limitations imposed by node-dota2 prevent lobbies from being configured past creation, meaning options like All Chat and cheats cannot be changed.  Lobby chat also cannot be joined.  If these things bother you, complain to rjackson about it.  

Unlike most commands, this command parses options using argparse.  The first option will be the top level items in the Arguments section, and additional options are defined using `-option value` format.

##### Category: `Dota`
##### Permission: `Broadcaster`
<!-- ##### Typical output: `` -->
##### Cooldown: `0 seconds`
##### Arguments:
  * `create` - Create a new lobby.  Only one lobby can be active at a time, across all instances of borkedbot using a particular steam account.
    - `-name lobbyname` - Name of the lobby.  May contain spaces.  Defaults to "Borkedbot lobby".
    - `-mode gamemode` - Sets the lobby gamemode.  Gamemodes are lowercase abreviations of the full name.  Defaults to All Pick.
      + `ap` - All Pick
      + `cm` - Captains Mode
      + `rd` - Random Draft
      + `sd` - Single Dragt
      + `ar` - All Random
      + `rcm` - Reverse Captains Mode
      + `mo` - Mid Only
      + `lp` - Least Played
      + `lh` - Limited Heroes
      + `ad` - Ability Draft
      + `ardm` - All Random Death Match (ARDM)
      + `1v1` - 1 vs 1 Mid
      + `rap` - Ranked All Pick (All Draft)
    - `-server region` - Defines which server the game will be hosted on.  Defaults to Automatic.
      + `auto`
      + `uswest`
      + `useast`
      + `europe`
      + `korea`
      + `singapore`
      + `australia`
      + `stockholm`
      + `austria`
      + `brazil`
      + `southafrica`
      + `perfectworldtelecom`
      + `perfectworldunicom`
    - `-password pass` - Sets the password for the lobby.
    - `-randompassword` - Generates a random password for the lobby.  This option is mutally exclusive with the `-password` option.  Note: There is as of yet no way for the streamer to know what password was generated.  This will be fixed in the future, probably by having borkedbot message the password to the streamer on steam.  
  * `leave` - Leaves the current lobby.  Lobbies will automatically be left once the game has started.
  * `remake` - Re-creates the lobby, leaving the old one and generating a new one.  Can use all options that `create` can.
  * `start` - Starts the game and leaves the lobby.
  * `shuffle` - Preforms a balanced shuffle of the players in the lobby.
  * `flip` - Switches the teams of all players in the lobby.
  * `kick` - Kicks a player from the lobby.  _Not yet implemented._
  * `status` - Displays if a lobby is in use.  _Functional, but unfinished._
  * `showpassword` - Displays the lobby password in chat.  Usually used when deciding to open the lobby up to all users in chat.
  * `help` - Displays a list of lobby options.  This list is probably what you want though.


## Channel Specific Commands
These commands are not related to a specific feature, but rather made or function for specific channels only.  Currently all commands are defined in [chatrules.py](modules/chatrules.py), but this will change after the command overhaul.


### `!mumble`
Displays information about the mumble server.

<!-- ##### Category: `Limited channels` -->
##### Channels: `monkeys_forever` `superjoe`
##### Permission: `All`
##### Typical output: `{address} 100 slot open server, on 24/7.  Don't be an idiot, etc...`
##### Cooldown: `15 seconds`


## monkeys_forever


### `!leaderboard`
### `!leaderboards`
Displays monkeys_forever's rank and MMR on the official [Dota 2 leaderboards](http://dota2.com/leaderboards/#americas).

<!-- ##### Category: ` ` -->
<!-- ##### Channels: `monkeys_forever` -->
##### Permission: `All`
##### Typical output: `Leaderboard data on rank and MMR with time of last update.`
##### Cooldown: `15 seconds`

---

### `!guildinvite [steam thing]`
### `!guildinvite [target user] [steam thing]` Mods only
Attempts to invite user to monkeys_forever's subscriber guild.  Subscribers only have one invite slot.  Successfully using the command again will kick the previously invited person from the guild.  Mods may designate a user to invite if needed.

<!-- ##### Category: ` ` -->
<!-- ##### Channels: `monkeys_forever` -->
##### Permission: `Subscribers`
##### Typical output: `Success message, error message, or help message, depending on user supplied argument.`
##### Cooldown: `0 seconds`
##### Arguments:
`[steam thing]` - Some reference to a user's steam account.  Uses the same input resolution code that `!mmrsetup` does, see [arguments](#arguments-6) for reference.
`[target user]` - __Mods only__ - Name of user to manually invite, if they for some reason cannot figure out what user they are.

---

### `!lastmatch`
### `!lastgame`
Returns the Dota 2 post-match blurb for the previous game.  Will be a Feature Specific command in the future.

<!-- ##### Category: ` ` -->
<!-- ##### Channels: `monkeys_forever` -->
##### Permission: `All`
##### Typical output: `The usual "{streamer} las won/lost a game" message.`
##### Cooldown: `30 seconds`

---

### `!music [user]`
### `!playlist [user]`
### `!songlist [user]`
Returns the link to monkeys_forever's playlist.

<!-- ##### Category: ` ` -->
<!-- ##### Channels: `monkeys_forever` -->
##### Permission: `All`
##### Typical output: `{user}: Monkeys' playlist can be found here: {link}`
##### Cooldown: `10 seconds`
##### Arguments:
`[user]` - Prepends the output with the supplied user instead of the one who invoked the command.

---

### `!song [user]`
### `!songname [user]`
### `!currentsong [user]`
Encourages the user to widen their occular orifices.  The song is always in the top left guys.  It always has been, and always will.  Sorry mobile quality users.

<!-- ##### Category: ` ` -->
<!-- ##### Channels: `monkeys_forever` -->
##### Permission: `All`
##### Typical output: `{user}: The name of the song is in the top left of the stream.  Open your eyeholes!`
##### Cooldown: `10 seconds`
##### Arguments:
`[user]` - Prepends the output with the supplied user instead of the one who invoked the command.


---

### `!background [user]`
Gives the user instructions on how to do the persistant loading screen background bug in Dota 2.  Some have said that only `dota_embers 0` is need but I'm not convinced.

<!-- ##### Category: ` ` -->
<!-- ##### Channels: `monkeys_forever` -->
##### Permission: `All`
##### Typical output: `{user}: It's a bug with the TI2 animated background.  Launch option: "-dashboard international_2012" Console command: "dota_embers 0"  Then close, open, and close your console, and play a game.`
##### Cooldown: `10 seconds`
##### Arguments:
`[user]` - Prepends the output with the supplied user instead of the one who invoked the command.

---

### `!greenarrow [user]`
### `!rangefinder [user]`
Gives the user the console command to enable the range finder in Dota 2.

<!-- ##### Category: ` ` -->
<!-- ##### Channels: `monkeys_forever` -->
##### Permission: `All`
##### Typical output: `Here's the console command: dota_disable_range_finder 0`
##### Cooldown: `10 seconds`
##### Arguments:
`[user]` - Prepends the output with the supplied user instead of the one who invoked the command.

---

### `!pudgefail [user]`
### `!pudgefails [user]`
### `!fountainhooks [user]`
Oh well monkeys, you tried your best.

<!-- ##### Category: ` ` -->
<!-- ##### Channels: `monkeys_forever` -->
##### Permission: `All`
##### Typical output: `rip root http://www.youtube.com/watch?v=7ba9nCot71w&hd=1`
##### Cooldown: `10 seconds`
##### Arguments:
`[user]` - Prepends the output with the supplied user instead of the one who invoked the command.


## superjoe

### `!youtube`
### `!twitter`
Links to plug superjoe's various things of intrest.

<!-- ##### Category: ` ` -->
<!-- ##### Channels: ` ` -->
##### Permission: `All`
##### Typical output: `links`
##### Cooldown: `10 seconds`

---

### `!ytmnd`
Courtesy of Slayerx1177

<!-- ##### Category: ` ` -->
<!-- ##### Channels: ` ` -->
##### Permission: `All`
##### Typical output: `link to the superjoe ytmnd page`
##### Cooldown: `10 seconds`

---

### `!plugs`
Convience command for listing the youtube and twitter links.

<!-- ##### Category: `` -->
<!-- ##### Channels: `` -->
##### Permission: `All`
##### Typical output: `both youtube and twitter links`
##### Cooldown: `10 seconds`

---

### `!time`
Returns the current time where superjoe is (EST).

<!-- ##### Category: `` -->
<!-- ##### Channels: `` -->
##### Permission: `All`
##### Typical output: `It is {date and time} in {random silly flavor text about where superjoe is}.`
##### Cooldown: `10 seconds`

---

#### Town of Salem related commands are disabled for the time being.

---

## unsanitylive

### `!plugs`
Convience command for listing the facebook and twitter links.

<!-- ##### Category: `` -->
<!-- ##### Channels: `` -->
##### Permission: `All`
##### Typical output: `both facebook and twitter links`
##### Cooldown: `10 seconds`

---






<!--

### `!command []`
Text about the command

##### Category: ``
##### Channels: ``
##### Permission: ``
##### Typical output: ``
##### Cooldown: ``
##### Arguments:
`[ ]` - Blah

---

 -->

## Modules
<!-- The white zone is for dynamic module loading and unloading only.  There is no parking in the white zone. -->

### Current modules
<!-- Blah blah something about the top level files  -->

#### chatrules.py
Main file for commands.  All commands are created and processed from this file.  The command system is pending overhaul, and will be removed in favor per channel importing.

#### chatlogger.py
Logs chat to a file.  Can be used in conjunction with an IRC stats page like [this](http://singstats.io).

#### command.py
Command class definition file.  Used by chatrules.py for processing commands.  Pending command system overhaul.

#### cosmo_rng.py
Silly module made for cosmo. See [this tweet](https://twitter.com/cosmowright/status/535216896069890048).

#### dota.py
Interfaces with the node process and steam api to provide dota/steam related functionality.

  * Accurate MMR data on request for enabled streamers.  Requires adding the bot as a friend on steam and public profile.
  * Post match data with MMR difference, steam api allowing.  Match information is gathered from the steam api, while MMR difference requires the previously mentioned condition.
  * Mentioning of notable players in game.  Notable players are definied as the Dotabuff Verified Players list plus streamers.  (WORK IN PROGRESS, NOT YET COMPLETE)
  * Lobby management.  Limited by node-dota2 functionality.  Work on this feature will be resumed during the subgames introduction.
  * Helper functions for steam related things.

#### extraevents.py
Module for unsorted, testing or temporary events that have no proper parent module.  Code here is usually temporary and will be moved to its own module eventually.

#### hosting.py
Events related to dealing with hosted channels on twitch.

  * Says message upon notification that a stream is being hosted.
  * Automatic unhosting of channels after target channel is offline for an arbritrary ammount of time. (FEATURE BROKEN, CURRENTLY DISABLED)

#### markov.py
Takes messages from twitch chat and breaks them up for use in markov chains.  Sentences generated from the current databade are probably run on sentences and reference Dota in some way.  Don't say I didn't warn you.

#### moderation.py (not commited)
Moderation rules for channels.  Will not be commited for obscurity purposes.

#### node.py
Interface for the node-steam process.  Contains mostly wrapper functions to ensure arguments are passed properly.

#### reaction.py
Some weird system I thought up some day, started, made 0 progress on, and forgot about.  May or may not be deleted.

#### recurring.py
Module for handling recurring events, triggered by the `timer` event from the main bot.

#### settings.py
Interface for redis database.  Keys are stored in python pickle format for convient storage and parsing of complex python constructs.

#### steamapi.py
Interface for the Steam API.  Access key is required.  (TODO: add link to steam dev page thing)

#### twitchapi.py
Interface for the Twitch API.  Key does not seem to be required but may be in the future.

### Planned updates and features

  * Command overhaul
  * More mmr stuff tracking or whatever
  * timed key addition to settings
  * fix auto unhosting
  * folder module loading for import overhaul
  * addition of information to the borkedbot steam page (online/ingame/offline etc)
  * Multiple dota accounts, switching depending on which one is in game

I guess that's good enough for now I'll add more later.
