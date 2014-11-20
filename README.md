borkedbot
=========

Custom, extensible, work in progress chatbot for twitch.

Borkedbot is a python IRC bot built for twitch.tv chats.  It interfaces with Steam and Dota 2 through node-steam and node-dota2, along with accessing the Steam and Twitch APIs.  Borkedbot currently runs on Python 2.7 in a linux environment.  No guarentees are made about stability, and some features are limited by the twitch and steam API's availablity.  

Dependencies
------------

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

For Steam and Dota 2 related functionality a running instance of node-steam with node-dota2 is required.  See [dota.js](modules/node/dota.js) for more information. 

Features
--------

Borkedbot is designed to be interfaced almost entirely through chat.  Redis settings keys may be manually changed for debugging or maintence reasons, but is usually not needed.  It should be noted that keys are in python pickle format.  Importing the settings module from an interpreter is the suggested method of interaction.

### Current modules

#### chatrules.py
Main file for commands.  All commands are created and processed from this file.  The command system is pending overhaul, and will be removed in favor per channel importing.

#### chatlogger.py
Logs chat to a file.  Can be used for an IRC stats page like [this](http://singstats.github.io).

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
Interface for the Twitch API.  Key may not be required but you might as well.  

### Commands
Please don't make me write this tonight.

### Planned updates and features

  * Command overhaul
  * More mmr stuff tracking or whatever
  * timed key addition to settings
  * fix auto unhosting
  * folder module loading for import overhaul
  * addition of information to the borkedbot steam page (online/ingame/offline etc)
  
I guess that's good enough for now I'll add more later.
