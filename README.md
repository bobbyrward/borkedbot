# borkedbot

Custom, extensible, work in progress chatbot for twitch.

Borkedbot is a python IRC bot built for twitch.tv chats.  It interfaces with Steam and Dota 2 through node-steam and node-dota2, along with accessing the Steam and Twitch APIs.  Borkedbot currently runs on Python 2.7 in a linux environment.  No guarentees are made about stability, and some features are limited by the twitch and steam API's availablity.  

## Dependencies

Python modules required:

  * twisted
  * redis
  * requests
  * dill
  * dateutil

Other:

  * node-steam
  * node-dota2
  * steam api access
  * twitch api access

For Steam and Dota 2 related functionality a running instance of node-steam with node-dota2 is required.  See [modules/node/dota.js](dota.js) for more information.

# Features

Borkedbot is designed to be interfaced almost entirely through chat.  Redis settings keys may be manually changed for debugging or maintence reasons, but is usually not needed.  It should be noted that keys are in python pickle format.  Importing the settings module from an interpreter is the suggested method of interaction.

<!-- Blah blah something about automatic messages like the dota blurb -->

# Commands
Commands are currently created manually per channel, with some that can be used across channels.  Part of the command overhaul will be the ability to create simple commands through chat.  Complex commands may still need to be created manually.  The command system may include a way to generate an information page automatically or on demand in the future.  

Commands have varying levels of permissions and rules regarding when and in which channels they are active for.  They can be disabled per channel by request of the channel owner.  Commands that only work for the bot host (imayhaveborkedit) will be ommited due to irrevelance to the following section.

## Current commands 
###### List is highly subject to change, see [modules/chatrules.py](chatrules.py) for the most current commited commands.

### Arguments
  * `[arg]` - Optional argument.
  * `<arg>` - Required argument.
  * `'arg'` - Literal argument.  The word in quotes _is_ the argument.  Multiple arguments are considered literals as well.
  * `arg1 | arg2` - Multiple arguments.  Either can be used, ex: `!command arg1` or `!command arg2`

### Permissions heirarchy
The permissions tree is as follows.  Highest permissions on the left, lowest on the right.

`Special` - `Broadcaster` - `Mods` - `Subscribers` - `All`

##### Special
Only the bot host (imayhaveborkedit) can use these.  Usually reserved for test commands or other convience commands.

The rest should be self explainatory.

### Global commands
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
`[two word seed]` - Takes two words and tried to create a sentence using those to start with.  Typically inferior to using the command without the argument.

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

### I-forgot-what-I-was-going-to-call-these commands
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
Text about the command

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
Text about the command

##### Category: `Dota`
##### Permission: `Broadcaster`
##### Typical output: `Depends on argument.  Command will attempt to guide you through the setup process.`
##### Cooldown: `5 seconds`
##### Arguments:
  * `[help]` - Displays information about the command.
  * `[addyou]` - Returns borkedbot's steam profile link and a steam uri link for use with the `Win+R` Run dialog.
  * `[addme]` - Requests that borkedbot attempt to add the broadcaster from...
    * `<steam thing>` - A steam profile link, id, vanity name, dota id, etc.  Valid items are:
      * steam community link _TODO_
      * steam community id _TODO_
      * steam community vanity name _TODO_
      * dota id _TODO_
      * that other steam id thing _TODO_
  * `[verify]` - Verifies the streamer with borkedbot and enables dota related features in the channel.
    * `<code>` - Code given to the streamer by borkedbot through steam chat to verify themselves.

---

### `!dotaconfig [status | setname | enable <dota | mmr> | disable <dota | mmr>]`
Configuration command for dota related settings.  More options will be added in the future.

##### Category: `Dota`
##### Permission: `Broadcaster`
##### Typical output: `Depends on argument.  No help argument available yet, use this for reference.`
##### Cooldown: `5 seconds`
##### Arguments:
`[status]` - Blah

To be continued...
---



<!-- 
### `!command [ ]`
Text about the command

##### Category: ` `
##### Permission: ` `
##### Typical output: ` `
##### Cooldown: ` `
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
  
I guess that's good enough for now I'll add more later.