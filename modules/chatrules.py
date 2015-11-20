# -*- coding: utf-8 -*-
import sys
sys.dont_write_bytecode = True

import os, time, math, random, re, redis
import markov, command, chatlogger, settings, steamapi, twitchapi
from command import get_process_output

LOAD_ORDER = 20

magic8ball = ["it is certain.",
    "it is decidedly so.",
    "without a doubt.",
    "yes definitely.",
    "you may rely on it.",
    "as I see it, yes.",
    "most likely.",
    "outlook good.",
    "yes.",
    "signs point to yes.",
    "better not tell you now.",
    "cannot predict now.",
    "don't count on it.",
    "my reply is no.",
    "my sources say no.",
    "outlook not so good.",
    "very doubtful.",
    "SSSSHHHHHHH",
    "Kappa",
    "no, you fucking mongoloid.",
    "go suck a dick."]


message_commands = []
joinpart_commands = []

global_channel_blacklist = []

def setup(bot):
    reload(command)

    generate_message_commands(bot)


def alert(event):
    if event.etype == 'msg':
        if event.channel in global_channel_blacklist:
            return

        tstart = time.time()
        for comm in message_commands:
            t1 = time.time()

            # TODO: Catch error and return that

            output = comm.process(event.channel, event.user, event.data, _getargs(event.data))
            t2 = time.time()
            if output[1] is command.OK:
                # print "[Chatrules] Output for %s: %s" % (comm.trigger, output[0])
                print "[Chatrules] '%s': %4.4fms, Total time: %4.4fms" % (comm.trigger, (t2-t1)*1000, (t2-tstart)*1000)
                event.bot.botsay(output[0])

def _getargs(msg):
    try:
        a = msg.split()
    except:
        return list()
    if len(a) == 1:
        return list()
    else:
        return a[1:]


def generate_message_commands(bot):
    # generate_special_commands()
    # generate_general_commands()
    # generate_channel_commands()
    global message_commands
    coms = []


    #############################
    #
    # SPECIAL RESTRICTED message_COMMANDS
    #
    #############################

    me_only_group = ['special']
    me_and_broadcaster = ['special', 'broadcaster']

    coms.append(command.SimpleCommand('!dbsize', "We've got %s word pairs." % markov.redis_conn.dbsize(), bot, groups=me_only_group, prependuser=False))

    # Exec #

    def f(channel, user, message, args, data, bot):
        print "Executing: %s" % message[7:]
        try:
            exec message[7:] in globals(), locals()
        except Exception as e:
            print "Something fucked up: %s" % e
            return "You borked something: %s" % e
    coms.append(command.Command('#!exec', f, bot, groups=me_only_group))

    # Eval #

    def f(channel, user, message, args, data, bot):
        print "Evaluating: %s" % message[7:]
        try:
            mout = str(eval(message[7:])).replace('\n', ' - ')
            if len(mout) > 350:
                print '#'*20
                print mout
                print '#'*20
                return "Output is too long!  See console."
            else:
                return mout
        except Exception as e:
            print "Something fucked up: %s" % e
            return "You borked something: %s" % e
    coms.append(command.Command('#!eval', f, bot, groups=me_only_group))

    def f(channel, user, message, args, data, bot):
        import settings

        if args:
            if args[0] in ['len', 'size']:
                return str(settings.numkeys())

            elif args[0] in ['get']:
                return str(settings.getdata(args[1]))

            elif args[0] in ['set']:
                try:
                    coer=eval(args[3])
                    if coer == bool:
                        coer = eval
                except:
                    coer=str

                try:
                    oldval = settings.getdata(args[1])
                except:
                    settings.setdata(args[1], coer(args[2]))
                    return "Key %s added: %s (%s)" % (args[1], args[2], (coer.__name__ if coer is not eval else bool.__name__))
                else:
                    settings.setdata(args[1], coer(args[2]))
                    return "Key %s changed: %s -> %s (%s)" % (args[1], oldval, args[2], (coer.__name__ if coer is not eval else bool.__name__))

            elif args[0] in ['remove', 'delete', 'del']:
                try:
                    settings.deldata(args[1])
                except:
                    return "Key %s does not exist." % args[1]
                else:
                    return "Key %s deleted." % args[1]

            elif args[0] in ['dump']:
                print settings.dumpkeys()
                return 'Done, see console.'

            # Else just presume that the arg is a settings domain
        return 'Huh?'
    coms.append(command.Command('#!settings', f, bot, groups=me_only_group))

    coms.append(command.SimpleCommand('!battlestation', 'HONK http://i.imgur.com/MRuOzd2.jpg', bot, True, groups=me_only_group))

    def f(channel, user, message, args, data, bot):
        import settings, dota
        if args:
            player_datas = settings.getdata('dota_notable_players')

            if args[0] == 'add':
                try:
                    new_player_id = int(args[1])
                    new_player_name = ' '.join(args[2:])
                except:
                    return 'Usage: !notable add dotaid playername'
                else:
                    if player_datas.get(int(args[1])):
                        return "This id belongs to %s, use the 'rename' option to change it." % player_datas.get(new_player_id)
                    player_datas[new_player_id] = new_player_name
                    settings.setdata('dota_notable_players', player_datas, announce=False)
                    return "%s registered as a notable player." % new_player_name

            elif args[0] == 'remove' and len(args) == 2:
                try:
                    player_id = int(args[1])
                except:
                    return "Bad player id"
                else:
                    if player_id in player_datas:
                        rip = player_datas[player_id]
                        del player_datas[player_id]
                        settings.setdata('dota_notable_players', player_datas, announce=False)
                        return "Removed %s from notable player list." % rip
                    else:
                        return "That id is not in the list."

            elif args[0] == 'rename':
                try:
                    player_id = int(args[1])
                    new_name = ' '.join(args[2:])
                except:
                    return "Bad player id"
                else:
                    if player_id in player_datas:
                        old_name = player_datas[player_id]
                        player_datas[player_id] = new_name
                        settings.setdata('dota_notable_players', player_datas, announce=False)
                        return "Player name changed: %s -> %s" % (old_name, new_name)
                    else:
                        return "That id is not in the list."

            elif args[0] == 'update':
                changed = dota.update_verified_notable_players()
                return "Updated list, %s entries changed." % changed

            elif args[0] == 'reset':
                settings.setdata('%s_notable_last_check' % channel, 0.0)
                settings.setdata('%s_notable_message_count' % channel, 10000)

    coms.append(command.Command('!notable', f, bot, groups=me_only_group))


    ######################################################################
    # Broadcaster/me message_commands
    #


    def f(channel, user, message, args, data, bot):
        import twitchapi, datetime, dateutil.parser, dateutil.relativedelta

        isotime = twitchapi.get('users/%s' % args[0], 'created_at')
        t_0 = dateutil.parser.parse(isotime)
        t_now = datetime.datetime.now(dateutil.tz.tzutc())
        reldelta = dateutil.relativedelta.relativedelta(t_now, t_0)
        reldelta.microseconds = 0

        return str(reldelta).replace('relativedelta','').replace('+','').replace('(','').replace(')','')

    coms.append(command.Command('!accountage', f, bot, groups=me_and_broadcaster))


    def f(channel, user, message, args, data, bot):
        import string, random, argparse
        import node, settings
        from dota import Lobby


        if not node.gc_status():
            return "The dota 2 network is down (or the bot has disconnected for some reason)."

        try:
            lobby = settings.getdata('latest_lobby')
        except:
            lobby = None

        class UsefulArgumentParser(argparse.ArgumentParser):
            def error(self, message):
                # self.print_help(sys.stderr)
                raise ValueError(message)
                # self.exit(2, '%s: error: %s\n' % (self.prog, message))

        parser = UsefulArgumentParser('lobby')
        pwgroup = parser.add_mutually_exclusive_group()

        #def __init__(self, channel, name=None, password=None, mode=None, region=None):

        cmdoptions = ['create', 'leave', 'remake', 'start', 'shuffle', 'flip', 'kick', 'status', 'showpassword', 'help']

        parser.add_argument('option', choices=cmdoptions)
        parser.add_argument('-name', nargs='*', default='Borkedbot lobby', type=str)
        parser.add_argument('-mode', choices=Lobby.GAMEMODES.keys(), default='AP')
        parser.add_argument('-server', choices=Lobby.SERVERS.keys(), default='Auto', dest='region')
        pwgroup.add_argument('-password', nargs='*', default=argparse.SUPPRESS, type=str)
        pwgroup.add_argument('-randompassword', action='store_true', default=argparse.SUPPRESS) # ENHANCE with action or something

        try:
            ns = parser.parse_args(args)
        except ValueError as e:
            return str(e)

        prepasswordns = ns

        if hasattr(ns, 'randompassword'):
            ns.password = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(7))
            del ns.randompassword

        option = ns.option
        del ns.option


        if option == 'create':
            if lobby:
                return "A lobby already exists (%s)" % lobby.chanel

            lobby = Lobby(channel, **vars(ns))
            lobby.create()
            settings.setdata('latest_lobby', lobby)

            return "A LOBBY HAS BEEN CREATED %s" % str(prepasswordns).replace('Namespace','')


        elif option == 'leave':
            if lobby:
                lobby.leave()
                settings.deldata('latest_lobby')
                return "Lobby has been abandoned."

        elif option == 'remake':
            if lobby:
                lobby.remake(**vars(ns))
                return "Lobby remade with options: %s" % str(prepasswordns).replace('Namespace','')

        elif option == 'start':
            if lobby:
                lobby.start()
                lobby.leave()
                return

        elif option == 'shuffle':
            if lobby:
                lobby.shuffle()
                return

        elif option == 'flip':
            if lobby:
                lobby.flip()
                return

        elif option == 'kick':
            if lobby:
                return 'Not yet implemented'

        elif option == 'status':
            if not lobby:
                return "No lobby"
            else:
                return "Current lobby: yes (%s)" % lobby.channel # TODO: add __repr__

        elif option == 'showpassword':
            return "Here's the lobby password: %s" % lobby.password

        elif option == 'help':
            return "!lobby options: %s" % ', '.join(cmdoptions)

        return "How did something not happen.  That... shouldn't happen..."

    coms.append(command.Command('!lobby', f, bot, groups=me_and_broadcaster))

    def f(channel, user, message, args, data, bot):
        import recurring, twitchapi

        if args:
            if args[0] in ['new', 'add'] and len(args) >= 3:
                # register_new_recurring(bot, name, message, timeout, checkfunc, duration=None, autostart=False)
                name = args[1]
                timeout = int(args[2])
                message = ' '.join(args[3:])

                if "'" in name:
                    return 'Event names may not have apostrophes in them (no \')'

                recurring.register_new_recurring(bot, name, message, timeout, autostart=True)
                return "Recurring event '%s' created repeating every %s seconds." % (name, timeout)

            if args[0] in ['del', 'delete'] and len(args) >= 2:
                if recurring.delete_recurring(args[1]):
                    return "Event %s stopped and deleted." % args[1]
                else:
                    return 'That event does not exist, use the \'list\' argument to see what your events are.'

            if args[0] in ['delall', 'deleteall']:
                for r in recurring.list_recurring(channel):
                    if not r.endswith('_data'):
                        recurring.delete_recurring(r)

                return "All events deleted."

            if args[0] == 'start':
                try:
                    recurring.start_recurring(args[1])
                except:
                    return "Event already running"
                else:
                    return "Event %s started" % args[1]

            if args[0] == 'stop':
                try:
                    recurring.stop_recurring(args[1])
                except:
                    return "Event already stopped"
                else:
                    return "Event %s stopped" % args[1]

            if args[0] == 'skip':
                recurring.skip_recurring(args[1])

            if args[0] == 'status':
                if len(args) == 1:
                    # status all
                    statuses = {n:recurring.is_resurring_running(n) for n in recurring.list_recurring(channel) if not n.endswith('_data')}
                    for s in statuses:
                        statuses[s] = 'Running' if statuses[s] else 'Stopped'

                    return 'Event statuses: %s' % (str(statuses)[1:-1].replace('\'',''))
                else:
                    return '%s -> %s' % (args[1], 'Running' if recurring.is_resurring_running(args[1]) else 'Stopped')

            if args[0] == 'list':
                return 'Events: ' + ', '.join([n for n in recurring.list_recurring(channel) if not n.endswith('_data')])

            if args[0] == 'set' and len(args) >= 4:
                if args[1] == 'timeout':
                    if len(args) == 5:
                        now = 'now' in args[4]
                    else:
                        now = False

                    if recurring.set_timeout(args[2], int(args[3]), now):
                        return None if now else 'Ok, done.'
                    else:
                        return "Are you sure that's a thing?  I don't think it is."


            if args[0] == 'dump':
                print recurring.list_recurring(channel)
                return "I hope you find what you're looking for."

            return "unrecognized option %s, refer to usage here: https://github.com/imayhaveborkedit/borkedbot#arguments-5" % args[0]
        else:
            return "Refer to usage here: https://github.com/imayhaveborkedit/borkedbot#arguments-5"

    coms.append(command.Command('!recurring', f, bot, groups=me_and_broadcaster))


    def f(channel, user, message, args, data, bot):
        import twitchapi
        if args:
            sid = twitchapi.get_steam_id_from_twitch(args[0])
            sid = 'http://steamcommunity.com/profiles/%s' % sid if sid else 'No steam account linked to %s.' % args[0]
            return sid

    coms.append(command.Command('!twitch2steam', f, bot, True))

    def f(channel, user, message, args, data, bot):
        import twitchapi, dota
        if args:
            sid = dota.determineSteamid(args[0])
            if sid is None: return 'Could not resolve steam id.'
            twitchname = twitchapi.get_twitch_from_steam_id(sid)
            twitchname = twitchname if twitchname else 'No twitch account linked to this id.'
            return twitchname

    coms.append(command.Command('!steam2twitch', f, bot, True))

    ######################################################################
    # Mod message_commands
    #

    coms.append(command.SimpleCommand('Beep?', 'Boop!', bot, True, prependuser=False))

    coms.append(command.SimpleCommand(['!source', '!guts'], "BLEUGH https://github.com/imayhaveborkedit/borkedbot", bot, True, prependuser=True, repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand('!bursday', "Happy Bursday! http://www.youtube.com/watch?v=WCYzk67y_wc", bot, True))

    coms.append(command.SimpleCommand('!riot', 'ヽ༼ຈل͜ຈ༽ﾉ', bot, True, prependuser=False))
    coms.append(command.SimpleCommand('!shrug', '¯\_(ツ)_/¯', bot, True, prependuser=False))


    def f(channel, user, message, args, data, bot):
        return get_process_output('ddate', shell=True)
    coms.append(command.Command('!ddate', f, bot, True))

    def f(channel, user, message, args, data, bot):
        import re

        cat = ''
        if args:
            data = get_process_output('fortune -f', shell=True)

            cats = sorted([fl.strip() for fl in data.split('\n')[1:] if fl], reverse=True)
            catlist = [c.split()[1] for c in cats]
            noper_cats = ', '.join(catlist)

            if args[0].lower() == 'list':
                return ', '.join(noper_cats)
            elif args[0].lower() in catlist:
                cat = args[0].lower()
            else:
                return '%s is not a category.' % args[0]

        while True:
            try:
                out = get_process_output('fortune %s' % cat, shell=True).replace('\n', ' ').replace('\t','').strip()
            except Exception as e:
                return "Error: %s WutFace" % e
            re.sub('\s{2,}', ' ', out)
            if len(out) <= 400:
                # print list(out)
                return out

    coms.append(command.Command('!fortune', f, bot, True))

    def f(channel, user, message, args, data, bot):
        import re

        cat = '-o'
        if args:
            data = get_process_output('fortune -of', shell=True)

            cats = sorted([fl.strip() for fl in data.split('\n')[1:] if fl], reverse=True)
            catlist = [c.split()[1] for c in cats]
            noper_cats = ', '.join(catlist)

            if args[0].lower() == 'list':
                return ', '.join(catlist)
            elif args[0].lower() in catlist:
                cat = '/usr/share/games/fortunes/off/' + args[0].lower()
            else:
                return '%s is not a category.' % args[0]

        while True:
            try:
                out = get_process_output('fortune %s' % cat, shell=True).replace('\n', ' ').replace('\t','').strip()
            except Exception as e:
                return "Error: %s WutFace" % e
            re.sub('\s{2,}', ' ', out)
            if len(out) <= 400:
                # print list(out)
                return out

    coms.append(command.Command('!ofortune', f, bot, True))


    def f(channel, user, message, args, data, bot):
        import twitchapi

        if args: channel = args[0].lower()

        chatters = twitchapi.get_chatters(channel)
        num_chatters = chatters['chatter_count']

        try:
            num_viewers = twitchapi.get('streams/%s' % channel)['stream']['viewers']
        except:
            num_viewers = 0

        return 'Viewers: %s, Chatters: %s, Mods: %s%s%s' % (
            num_viewers, num_chatters, len(chatters['chatters']['moderators']),
            ', Admin: %s' % len(chatters['chatters']['admins']) if len(chatters['chatters']['admins']) else '',
            ', Staff: %s' % len(chatters['chatters']['staff']) if len(chatters['chatters']['staff']) else '')

    coms.append(command.Command('!chatters', f, bot, True, repeatdelay=15))

    def f(channel, user, message, args, data, bot):
        import node

        if args:
            if args[0].lower() == 'status':
                con_steam, con_dota = node.status()

                status_steam = "Ok" if con_steam else "Not ok"
                status_dota = "Ok" if con_dota else "Not ok"

                return "Connection status: Steam: %s | Dota: %s" % (status_steam, status_dota)

            if args[0].lower() == 'restart' and user == 'imayhaveborkedit':
                node.restart()

                return "Restarting steam bot, this should only take a few seconds."

            if args[0].lower() in ['matchmaking', 'mm']:
                # return "This breaks the bot.  Fix it first idiot."

                import difflib, time
                mmdata = node.get_mm_stats()

                try:
                    args[1]
                except:
                    args.append('USEast')

                # region = difflib.get_close_matches(args[1], mmdata.keys(), 1)[0]

                if args[1] == 'list':
                    return 'Matchmaking regions: %s' % ', '.join(mmdata.keys())

                if args[1].lower() == 'all':
                    return 'Matchmaking data for all regions: https://rjackson.me/tools/mmstats/'

                try:
                    lnames = {n.lower():n for n in mmdata.keys()}
                    region = [lnames[r] for r in difflib.get_close_matches(args[1].lower(), lnames, 1)][0]
                except:
                    return "No match for %s" % args[1]

                searchers = mmdata[region]

                return  "Matchmaking data for region %s: Players in queue: %s" % (region, searchers)

    coms.append(command.Command('!node', f, bot, True, repeatdelay=10))

    ######################################################################
    #
    # General message_commands
    #

    def f(channel, user, message, args, data, bot):
        import markov
        rngkey = '\x01'.join(args).lower() if len(args) == 2 else None
        print "Making something up using %s" % rngkey
        thing = markov.markov(rngkey).replace('kappa', 'Kappa')
        if thing in [None, '']:
            return "Uhhh... I got nothing."
        else:
            return thing

    coms.append(command.Command('!saysomething', f, bot, True, chanblacklist=['monkeys_forever'], repeatdelay=30))

    def f(channel, user, message, args, data, bot):
        if message.lower() in ['borkedbot, ?', 'borkedbot,?']:
            return "That's not even a real question."
        elif message.endswith('?'):
            # if message.lower().split(',')[1].strip().startswith('who'): return "%s, uhhh... you? Me? That guy? WutFace" % user
            # if message.lower().split(',')[1].strip().startswith('what'): return "%s,  WutFace" % user
            # if message.lower().split(',')[1].strip().startswith('when'): return "%s, look time is hard when the only numbers you're good with are 0 and 1 NotLikeThis" % user
            # if message.lower().split(',')[1].strip().startswith('where'): return "%s, http://maps.google.com Kappa" % user
            # if message.lower().split(',')[1].strip().startswith('why'): return "%s, because you smell bad WutFace" % user
            # if message.lower().split(',')[1].strip().startswith('how'): return "%s, because you smell bad WutFace" % user
            return "%s, %s" % (user, random.choice(data))

    coms.append(command.Command('Borkedbot,', f, bot, chanblacklist=['monkeys_forever', 'barnyyy'], data=magic8ball, repeatdelay=10))

    def f(channel, user, message, args, data, bot):
        import datetime, dateutil, dateutil.parser, dateutil.relativedelta, twitchapi, settings

        if args:
            channel = args[0].lower()
        streamdata = twitchapi.get('streams/%s' % channel.replace('#',''), 'stream')

        if streamdata is None:
            return "There is no stream D:"

        isotime = streamdata['created_at']

        t_0 = dateutil.parser.parse(isotime)
        t_now = datetime.datetime.now(dateutil.tz.tzutc())

        reldelta = dateutil.relativedelta.relativedelta(t_now, t_0)

        daystr = '{0.days} day'.format(reldelta)
        daystr += 's' if int(daystr.split()[0]) > 1 else ''

        hourstr = '{0.hours} hour'.format(reldelta)
        hourstr += 's' if int(hourstr.split()[0]) > 1 else ''

        minutestr = '{0.minutes} minute'.format(reldelta)
        minutestr += 's' if int(minutestr.split()[0]) > 1 else ''

        timestr = ', '.join([x for x in [daystr, hourstr, minutestr] if not x.startswith('0')])
        timestr = ' and '.join(timestr.rsplit(', '))

        if timestr:
            textstr = "{0}, {1} has been streaming for " + timestr + '.'
        else:
            textstr = "{0}, the stream just started."

        if not args and settings.getdata('%s_is_hosting' % channel):
            hc = settings.getdata('%s_hosted_channel' % channel)

            if hc and not args:
                streamdata = twitchapi.get('streams/%s' % hc, 'stream')
                channel = hc
                textstr += ' (hosted channel)'

        return textstr.format(user, channel) #+ " | Friendly reminder that BTTV has a /uptime command." if args else ''

    coms.append(command.Command('!uptime', f, bot, chanblacklist = ['mynameisamanda', 'gixgaming', 'bloodynine_'], repeatdelay=15))


    ######################################################################
    #
    # Channel spcifics
    #

    # Sort of general ######################################################

    def f(channel, user, message, args, data, bot):
        import json, os, time, settings, dota

        if channel == 'barnyyy':
            return '%s: 5k' % user

        if channel not in dota.enabled_channels.keys():
            print 'Channel not enabled for dota'
            return

        if channel in dota.enabled_channels.keys() and not dota.enabled_channels[channel][1]:
            if user == channel:
                rs = '''Hi %s, I can provide accurate MMR and automatically announce \
                games when they are finished with mmr change and totals. \
                All that is required is that you display your mmr on your profile card in dota. \
                Type "!mmrsetup" to get started (broadcaster only command).''' % channel
                return rs
            else:
                return

        mmrdata = dota.fetch_mmr_for_channel(channel)

        if not any(mmrdata):
            if user == channel:
                return "%s: If you want this command to work you have to display your mmr on your profile card now." % user
            else:
                return 'No MMR data available.'

        if all(mmrdata):
            return 'Solo: %s | Party: %s' % mmrdata
        elif mmrdata[0] is not None:
            return 'Solo: %s' % mmrdata[0]
        elif mmrdata[1] is not None:
            return 'Party: %s' % mmrdata[1]

    coms.append(command.Command('!mmr', f, bot, repeatdelay=10))

    def f(channel, user, message, args, data, bot): #TODO: rework this since the bot can't add people
        import dota, node, settings, twitchapi

        # return "I'm in the middle of rewriting this command. Don't worry it's almost done."

        if user not in [channel, 'imayhaveborkedit']:
            return

        if args:
            if args[0].lower() == 'help':
                helpstr = "If you've linked your steam and twitch accounts this command should just set everything up. "
                helpstr += 'Otherwise you need to supply a steam account, or dota id, or something like that.'
                return helpstr
            else:
                linked_id = args[0]
                if not linked_id:
                    return "I can't use that.  Give me something else."
        else:
            linked_id = twitchapi.get_steam_id_from_twitch(channel)

        if not linked_id:
            return "Unable to automatically setup mmr.  You'll need to supply some sort of steam account."

        ch_sid = dota.determineSteamid(linked_id)

        en_chans = settings.getdata('dota_enabled_channels')
        if channel in en_chans:
            return "You already set this up.  Ask imayhaveborkedit if you have a question."

        notablecheck = dota.enable_channel(channel, dota.ID.steam_to_dota(ch_sid), True, True)

        if notablecheck:
            return "All that's left is to add this one to the notable players list, then thats it.  Let imayhaveborkedit know of any bugs or issues, and remember to mod the bot."
        else:
            return "Ok, that should be it.  Let imayhaveborkedit know of any bugs or issues, and remember to mod the bot."

    coms.append(command.Command('!mmrsetup', f, bot, groups=me_and_broadcaster, repeatdelay=5))

    def f(channel, user, message, args, data, bot):
        import dota

        if channel not in dota.enabled_channels:
            return

        dotaid = settings.getdata('%s_dota_id' % channel)

        return '%s: http://www.dotabuff.com/players/%s' % (user, dotaid)

    coms.append(command.Command('!dotabuff', f, bot, repeatdelay=20))

    def f(channel, user, message, args, data, bot):
        '''
        setname/rename <name>
        enable <dota>
        disable <dota>
        '''
        import settings, dota, node
        if args:
            if args[0].lower() == 'status':
                return "This will be reworked."

                if channel not in dota.enabled_channels:
                    return "Channel is not enabled for dota."

                return "MMR is %s." % ('enabled' if dota.enabled_channels[channel][1] else 'disabled')

            if args[0].lower() in ['setname', 'rename'] and len(args) >= 2:
                newname = ' '.join(args[1:])

                try:
                    oldname = settings.getdata('%s_common_name' % channel)
                except:
                    oldname = channel

                settings.setdata('%s_common_name' % channel, newname)
                dota.update_channels()

                return "Set common name for %s: %s -> %s" % (channel, oldname, newname)

            if args[0].lower() == 'enable' and len(args) >= 2:
                if args[1] == 'dota':
                    dec = settings.getdata('dota_enabled_channels')
                    if channel in dec:
                        return "Channel already enabled"

                    dec = list(set(dec.append(channel)))
                    settings.getdata('dota_enabled_channels', dec)
                    dota.update_channels()

            if args[0].lower() == 'disable' and len(args) >= 2:
                if args[1] == 'dota':
                    dec = settings.getdata('dota_enabled_channels')
                    if channel not in dec:
                        return "Channel not enabled"

                    dec.remove(channel)
                    settings.setdata('dota_enabled_channels', dec)
                    dota.update_channels()

    coms.append(command.Command('!dotaconfig', f, bot, groups=me_and_broadcaster, repeatdelay=5))

    def f(channel, user, message, args, data, bot):
        import dota, settings, node

        if channel not in dota.enabled_channels:
            return

        # if user == 'bluepowervan' and not bot.user_is_op(user):
            # bot.botsay('.timeout bluepowervan 3840')
            # return "You know that doesn't work for you, stop trying."

        # if not bot.user_is_op(user) and user != 'imayhaveborkedit':
            # return

        if args:
            try:
                if not 1 <= int(args[0]) <= 10:
                    pages = 10
                else:
                    pages = int(args[0])
            except:
                pages = 10
        else:
            pages = 10

        playerid = settings.getdata('%s_dota_id' % channel)

        if node.get_user_status(dota.ID(playerid).steamid) == '#DOTA_RP_PLAYING_AS':
            playerheroid = dota.getHeroIddict(False)[node.get_user_playing_as(dota.ID(playerid).steamid)[0]]
        else:
            playerheroid = None

        if pages > 10 and playerheroid: pages = 10
        players, mmr = dota.searchForNotablePlayers(playerid, pages, playerheroid, True)

        if players is None:
            return "Game not found in %s pages." % pages

        if players:
            return "Notable players in this game: %s -- Average MMR: %s" % (', '.join(['%s (%s)' % (p,h) for p,h in players]), mmr)
        else:
            return "No other notable players found in the current game."

    coms.append(command.Command('!notableplayers', f, bot, repeatdelay=10))

    def f(channel, user, message, args, data, bot):
        import requests, re

        channelmap = { 'monkeys_forever': 'monkeys-forever', 'f4ldota': 'F4L' }

        if channel not in channelmap: return

        r = requests.get('http://neodota.com/rank/nel/ladder.php').text.replace(' ','')

        try:
            datas = str(re.search('.*<br\/>(<spanclass="rank">\d+</span><spanclass="player">'+ channelmap[channel] +'.+?<br/>?)', r).groups()[0])
            rank, name, rating, score, streak = re.findall('>([^<]+?)<', datas)
        except Exception as e:
            print e
            return "Error: something went horribly wrong"

        return "%s is rank %s with %s points, %s W/L and %s streak. See http://neodota.com/nel/ for more info." % (name, rank, rating.replace('(','').replace(')',''), score, streak)

    coms.append(command.Command('!nel', f, bot, repeatdelay=50))

    def f(channel, user, message, args, data, bot):
        namemap = {
            'monkeys_forever': 'monkeys-forever',
            'moodota2': 'Moo',
            'gixgaming': 'giX',
            'bloodynine_': 'Bloody Nine',
        }

        if channel not in namemap: return

        import json, requests, time, datetime, dateutil, dateutil.tz, dateutil.relativedelta
        lburl = "http://www.dota2.com/webapi/ILeaderboard/GetDivisionLeaderboard/v0001?division=americas"
        jdata = json.loads(requests.get(lburl).text)

        try:
            rank, mmr = {i['name']:(i['rank'],i['solo_mmr']) for i in jdata['leaderboard']}[namemap[channel]]
        except:
            return "Uhhh, about that..."

        ltime = time.localtime(int(jdata['time_posted']) + (time.altzone if time.daylight else time.timezone))

        lastupdate = time.strftime('%b %d, %I:%M%p',ltime)
        lt = datetime.datetime.fromtimestamp(time.mktime(ltime)).replace(tzinfo=dateutil.tz.tzutc())
        t_now = datetime.datetime.now(dateutil.tz.tzlocal())

        reldelta = dateutil.relativedelta.relativedelta(t_now, lt)

        daystr = ('{0} is rank {1} on the leaderboards, with {2} mmr. Last leaderboard update: '
            '{3.days} days, {3.hours} hours, {3.minutes} minutes ago - http://dota2.com/leaderboards/#americas')

        hourstr = ('{0} is rank {1} on the leaderboards, with {2} mmr. Last leaderboard update: '
            '{3.hours} hours, {3.minutes} minutes ago - http://dota2.com/leaderboards/#americas')

        minstr = ('{0} is rank {1} on the leaderboards, with {2} mmr. Last leaderboard update: '
            '{3.minutes} minutes ago - http://dota2.com/leaderboards/#americas')

        if reldelta.days:
            return daystr.format(channel, rank, mmr, reldelta).replace('rank 1 ', 'ヽ༼ຈل͜ຈ༽ﾉ rank 1 ヽ༼ຈل͜ຈ༽ﾉ ')
        elif reldelta.hours:
            return hourstr.format(channel, rank, mmr, reldelta).replace('rank 1 ', 'ヽ༼ຈل͜ຈ༽ﾉ rank 1 ヽ༼ຈل͜ຈ༽ﾉ ')
        else:
            return minstr.format(channel, rank, mmr, reldelta).replace('rank 1 ', 'ヽ༼ຈل͜ຈ༽ﾉ rank 1 ヽ༼ຈل͜ຈ༽ﾉ ')

    coms.append(command.Command(['!leaderboard', '!leaderboards'], f, bot, repeatdelay=15))

    def f(channel, user, message, args, data, bot):
        if args:
            doreset = len(args) >= 2
            if args[0] == 'steam':
                if doreset and args[1] == 'reset':
                    settings.setdata('%s_dota_last_steam_rss_update_url' % channel, '0')
                    return

                return settings.getdata('%s_dota_last_steam_rss_update_url' % channel)

            if args[0] == 'dota':
                if doreset and args[1] == 'reset':
                    settings.setdata('%s_dota_last_dota2_rss_update_url' % channel, '0')
                    return

                return settings.getdata('%s_dota_last_dota2_rss_update_url' % channel)

    coms.append(command.Command('!blog', f, bot, repeatdelay=30))


    # Monkeys_forever ######################################################

    def f(channel, user, message, args, data, bot):
        return "Guilds aren't even in reborn yet, chill."

        import twitchapi
        if not bot.user_is_sub(user):
            print user, 'is not a sub'
            if user != 'imayhaveborkedit' or not bot.user_is_op(user):
                return

        # Monkeys sub guild id: "228630"
        # Do check to see if "Is your name this thing I pulled from steam?"

        if not args:
            linked_id = twitchapi.get_steam_id_from_twitch(user)
            if linked_id:
                args.append(linked_id)
                print 'Found twitch linked id'
            else:
                return "%s: No linked steam account, you need to give me a steam id after the command, see: http://i.imgur.com/y7Fi4CA.png" % user

        if args:
            if args[0].lower() == 'help':
                return 'Usage: !guildinvite [steamid/profilename (needed if no linked steam account is found)]'

            import settings

            try:
                channelguildid = settings.getdata('%s_sub_guild_id' % channel)
            except:
                return "No sub guild id found for %s" % channel

            import dota, node, steamapi

            if len(args) == 1:
                targetsteamid = args[0]
                targetuser = user
            elif len(args) > 1 and bot.user_is_op(user):
                targetsteamid = args[1]
                targetuser = args[0]

            try:
                steamid = dota.determineSteamid(targetsteamid)
                if steamid == 76561198153108180:
                    return "%s: No, you're supposed to use your own account.  FailFish" % user
            except Exception as e:
                print e
                return "Something went wrong, it might be an issue with the steam api"

            if steamid:
                try:
                    previousinviteid = settings.getdata('invite_id_for_%s' % targetuser, domain='%s_sub_guild_invites' % channel)
                    previousinvitename = settings.getdata('invite_name_for_%s' % steamid, domain='%s_sub_guild_invites' % channel)

                except: # No data on record
                    previousinviteid = None
                    kick_result = None
                    invite_result = node.invite_to_guild(channelguildid, steamid)

                else: # ID already on record
                    if previousinviteid != steamid:
                        print "Attempting to kick %s" % previousinviteid
                        kick_result = node.kick_from_guild(channelguildid, previousinviteid)
                        print 'Kick result: %s' % kick_result

                    invite_result = node.invite_to_guild(channelguildid, steamid)


                if invite_result == 'SUCCESS':
                    settings.setdata('invite_id_for_%s' % targetuser, steamid, domain='%s_sub_guild_invites' % channel)
                    settings.setdata('invite_name_for_%s' % steamid, targetuser, domain='%s_sub_guild_invites' % channel)

                    try:
                        steamprofilename = steamapi.GetPlayerSummaries(str(steamid))['response']['players'][0]['personaname']
                    except Exception as e:
                        print 'Error getting steam profile name for %s:' % targetuser, e
                        steamprofilename = None

                    if kick_result:
                        return "%s%s has been invited to the sub guild. Make sure you have \"Allow guild invites from -> Anyone\" enabled." % (
                            targetuser, ' (%s)' % steamprofilename if steamprofilename else '')
                    else:
                        return "%s%s has been invited to the sub guild. Make sure you have \"Allow guild invites from -> Anyone\" enabled." % (
                            targetuser, ' (%s)' % steamprofilename if steamprofilename else '')
                else:
                    return "Invitation failure: %s" % invite_result.lower()
            elif steamid is False:
                return "Steam api down, cannot resolve vanity name"

            return "Bad id or something, I can't figure out who you are.  Try one of these: http://i.imgur.com/y7Fi4CA.png"
        else:
            return "%s: You need to give me a steam id or profile link, see http://i.imgur.com/y7Fi4CA.png" % user

    coms.append(command.Command('!guildinvite', f, bot, channels=['monkeys_forever', 'kizzmett']))

    def f(channel, user, message, args, data, bot):
        import dota
        return dota.latestBlurb(channel, True)

    coms.append(command.Command(['!lastmatch', '!lastgame'], f, bot, repeatdelay=60))

    def f(channel, user, message, args, data, bot):
        return "%s: rip grooveshark, see top left of stream" % user

        import requests

        try:
            r = requests.get('http://last.fm/user/monkeys-forever/now')

            r_nameindex = r.text.index('class="track-name')
            nameindex = r_nameindex + r.text[r_nameindex:].index('>') + 1
            songname = r.text[nameindex:].split('<')[0]

            artistname = r.text[r.text.index('<div class="artist-name">'):].split('>')[2].strip().split('\n')[0]

            # THIS IS SO AWFUL I KNOW I'M GOING TO REDO IT SOMETIME

            return 'Now Playing: ' + songname + ' -- ' + artistname
        except:
            return 'Something borked, just direct your eyeholes to the top left of the stream.'

    coms.append(command.Command(['!song', '!currentsong', '!songname'], f, bot, channels=['monkeys_forever'], repeatdelay=40))

    #coms.append(command.SimpleCommand(['!song', '!currentsong', '!songname'], 'The name of the song is in the top left of the stream.  Open your eyeholes!', bot,
    #    channels=['monkeys_forever'], repeatdelay=25, targeted=False))

    coms.append(command.SimpleCommand(['!music', '!playlist', '!songlist'],
        "https://play.spotify.com/user/monkeys-/playlist/7ob9QZOQi569vMVXh8GhDT", bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand('!songrequest', 'This aint no nightbot stream', bot, channels=['monkeys_forever'], repeatdelay=10))

    coms.append(command.SimpleCommand(['!fountainhooks', '!pudgefail', '!pudgefails'], 'rip root http://www.youtube.com/watch?v=7ba9nCot71w&hd=1',
        bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    # Barny #########################################################

    coms.append(command.SimpleCommand('!rightclick', 'dota_player_auto_repeat_right_mouse 1',
        bot, channels=['barnyyy'], targeted=True, repeatdelay=15))

    coms.append(command.SimpleCommand('!vectorpathing', 'dota_unit_allow_moveto_direction 1',
        bot, channels=['barnyyy'], targeted=True, repeatdelay=15))

    coms.append(command.SimpleCommand('!announcer', 'Weeaboo anime boatgirl announcer > https://www.youtube.com/watch?v=AQXQkDFE-sk',
        bot, channels=['barnyyy'], targeted=True, repeatdelay=15))

    # Superjoe ######################################################

    coms.append(command.SimpleCommand('!youtube', 'Subscribe to Superjoe on youtube!  https://www.youtube.com/user/WatchSuperjoe',
        bot, channels=['superjoe'], prependuser=False, targeted=True, repeatdelay=10))

    coms.append(command.SimpleCommand('!twitter', 'Follow Superjoe on Twitter!  http://twitter.com/superjoeplays',
        bot, channels=['superjoe'], prependuser=False, targeted=True, repeatdelay=10))

    coms.append(command.SimpleCommand('!ytmnd', 'http://superjoe.ytmnd.com (courtesy of Slayerx1177)',
        bot, channels=['superjoe'], prependuser=False, targeted=True, repeatdelay=10))

    coms.append(command.SimpleCommand('!plugs', 'Youtube: https://youtube.com/user/WatchSuperjoe | Twitter: http://twitter.com/superjoeplays | ' +
        'Like/Follow/Subscribe/whatever you want, that\'s where you can find Superjoe!',
        bot, channels=['superjoe'], prependuser=False, targeted=True, repeatdelay=10))


    def f(channel, user, message, args, data, bot):
        import random
        places = ["Superjoe Land.", "Superjoe's dirty hovel.", "Superjoe's shining kingdom.", "Superjoe's murky swamp.", "Superjoe's haunted house.",
        "Superjoe's secret cave under monkeys_forever's house.", "Superjoe's bathtub.", "Superjoe's slave dungeon.", "Superjoe's deflated bouncy castle.",
        "Superjoe's vault of broken promises and intangible dreams.", "Superjoe's corn field.", "Superjoe's questionable abode."]

        random.shuffle(places)

        return 'It is currently %s in %s' % (time.asctime(), random.choice(places))

    coms.append(command.Command('!time', f, bot, channels=['superjoe'], repeatdelay=15))


    # Tom ##############

    coms.append(command.SimpleCommand('!plugs', 'Links! http://www.facebook.com/unsanitylive | http://twitter.com/unsanitylive | ' +
        'http://steamcommunity.com/groups/Unsanitylive | https://www.speq.me/unsanitylive/ | ' +
        'Like/Follow/Subscribe/whatever you want, that\'s where you can find Tom!',
        bot, channels=['unsanitylive'], prependuser=False, repeatdelay=10))

    # Moo #############

    coms.append(command.SimpleCommand('!ohnohesretarded', 'http://i.imgur.com/ZdaV0PG.png', bot, channels=['moodota2', 'barnyyy', 'lamperkat'], targeted=True, repeatdelay=15))

    coms.append(command.SimpleCommand('!announcer', 'Weeaboo Onodera+Kongou waifu announcer > http://saylith.github.io/harem-announcer/',
       bot, channels=['moodota2'], targeted=True, repeatdelay=15))

    # B9 ###############################

    # coms.append(command.SimpleCommand(['!music', '!playlist', '!songlist'],
    #     "https://www.youtube.com/playlist?list=PLCUELUXNSjikxw-Utn8E_XrdjDLNm13IO", bot, channels=['bloodynine_'], repeatdelay=10))

    ######################################################################
    #
    # Test commands
    #

    def f(channel, user, message, args, data, bot):
        import dota, settings
        try:
            ccom = dota.getSourceTVLiveGameForPlayer(settings.getdata('%s_dota_id' % channel))['server_steam_id']
        except Exception as e:
            print e
            return "Game not found (or some other error)"
        return str('Dota console command: watch_server %s' % ccom)

    coms.append(command.Command('!watchgame', f, bot, repeatdelay=30))

    def f(channel, user, message, args, data, bot):
        import dota, settings, makegist

        try:
            pdata = dota.get_players_in_game_for_player(settings.getdata('%s_dota_id' % channel), checktwitch=True, markdown=True)
        except Exception as e:
            print e
            return "Unable to generate playerdata: %s" % str(e.message)

        print "Generated data" + ("" if pdata else "(but its empty)")
        if pdata is None:
            return 'Cannot find match.'

        addr = makegist.create_dota_playerinfo(channel, pdata, shorten=True)
        return "Player info for this game is available here: %s" % addr

    coms.append(command.Command('!playerinfo', f, bot, repeatdelay=30, groups=me_and_broadcaster))


    def f(channel, user, message, args, data, bot):
        import time

        if not args:
            return "You know you're supposed to give me names to unban right?  Maybe you were looking for bttv /massunban"

        sleeptime = 0.4

        bot.botsay("Unbanning %s names, will be completed in %s seconds." % (len(args), sleeptime*len(args)))

        for name in args:
            try:
                bot.botsay('.unban ' + name.lower())
            except:
                bot.botsay("Bad name: " + name)
                print "Bad name: " + name
            time.sleep(sleeptime)

    coms.append(command.Command('!massunban', f, bot, repeatdelay=30, groups=me_and_broadcaster))

    def f(channel, user, message, args, data, bot):
        import twitchapi, datetime, dateutil.parser

        if args:
            followinguser = args[0]
            if len(args) > 1:
                targetuser = args[1]
            else:
                targetuser = channel

            try:
                userdata = twitchapi.get('users/%s/follows/channels/%s' % (followinguser.lower(), targetuser.lower()))
            except:
                return "Either they don't follow that user or the twitchapi borked"

            isotime = userdata['created_at']

            t_0 = dateutil.parser.parse(isotime)
            t_now = datetime.datetime.now(dateutil.tz.tzutc())
            reldelta = dateutil.relativedelta.relativedelta(t_now, t_0)

            reldelta.microseconds = 0
            strdelta = str(reldelta).replace('relativedelta','').replace('+','').replace('(','').replace(')','')

            listdelta = strdelta.split(', ')
            for x in xrange(0, len(listdelta)):
                if listdelta[x].endswith('s=1'):
                    listdelta[x] = listdelta[x].replace('s=1', '=1')

            timedata = [ ' '.join(reversed(x.split('='))) for x in listdelta]

            return "[Not sure if accurate] %s has followed %s for %s... maybe?" % (followinguser, targetuser, ', '.join(timedata))

            # years=1, months=2, days=22, hours=12, minutes=42, seconds=16

    coms.append(command.Command('!followingsince', f, bot, True, groups=me_only_group))


    def f(channel, user, message, args, data, bot):
        import twitchapi, random

        chatters = twitchapi.get_chatters(channel)['chatters']
        return 'I choose %s!' % random.choice(chatters['viewers'] + chatters['moderators'] + chatters['staff'] + chatters['admins'])

    coms.append(command.Command('!randomviewer', f, bot, True))


    def f(channel, user, message, args, data, bot):
        import twitchapi

        if len(args) == 1:
            basechannel = channel
            targetchannel = args[0]
        elif len(args) == 2:
            basechannel = args[0]
            targetchannel = args[1]

        basechatters = set(twitchapi.get_chatters_list(basechannel.lower()))
        targetchatters = set(twitchapi.get_chatters_list(targetchannel.lower()))

        print '======'
        print [str(c) for c in basechatters & targetchatters]
        print '======'

        return 'There are %s people in both chats' % len(basechatters & targetchatters)

    coms.append(command.Command('!crosschat', f, bot, True))

    # def f(channel, user, message, args, data, bot):
    #     if args:
    #         if args[0] == 'start':
    #             pass
    #     else:
    #         return 'this is the help text'
    # coms.append(command.Command('!adventure', f, bot, True, groups=me_and_broadcaster)) # This is never going to happen


    def f(channel, user, message, args, data, bot):
        import random
        if args:
            try:
                dice, sides = args[0].lower().split('d')


                dice = int(dice)
                sides = int(sides)
                rolls = []
            except:
                return 'Hmmm, you borked something.  Example: !roll 2d10'

            for x in range(dice):
                rolls.append(random.randrange(1, sides))

            return '%s: %s -> %s %s' % (user, args[0], sum(rolls), str(rolls).replace('[', '(').replace(']', ')'))

        else:
            return '%s: 1d6 -> %s' % (user, random.randint(1,6))
    coms.append(command.Command('!roll', f, bot, True))


    def f(channel, user, message, args, data, bot):
        import node, dota, twitchapi

        linked_id = twitchapi.get_steam_id_from_twitch(user)
        if not linked_id:
            return '%s: I dunno! Link your steam and twitch accounts in your twich settings!' % user

        tsid = dota.determineSteamid(linked_id)

        smmr, pmmr = node.get_mmr_for_dotaid(dota.ID(tsid).dotaid)

        if smmr is not None:
            return '%s: %s!' % (user, smmr)
        elif pmmr is not None:
            return '%s: %s!' % (user, pmmr)
        else:
            return '%s: I dunno! Stop hiding your mmr!' % user

    coms.append(command.Command('!mymmr', f, bot, repeatdelay=1))


    ######################################################################

    message_commands = coms

    return "Generated %s message commands" % len(message_commands)

