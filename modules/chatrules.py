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

salem_townies = {
    'bodyguard' : ('Bodyguard', 'Town Protective',
        'Protect one person from death each night. If your target is attacked both you and your attacker will die instead. Your counterattack ignores night immunity. (One bulletproof vest)'),
    'doctor' : ('Doctor', 'Town Protective',
        'Heal one person each night, preventing them from dying. You will know if your target is attacked. (One self heal)'),
    'escort' : ('Escort', 'Town Support',
        'Distract someone each night. Prevents them from acting. If you target a Serial Killer they will attack you instead.'),
    'investigator' : ('Investigator', 'Town Investigative',
        'Investigate one person each night for a clue to their role. Framed players will appear to be a Framer.'),
    'jailor' : ('Jailor', 'Town Killing',
        'You may choose one person during the day to jail for the night. You anonymously speak to '+
        'and can choose to execute your prisoner. Prisoner is roleblocked an immune. (many caveats, see wiki)'),
    'lookout' : ('Lookout', 'Town Investigative',
        'Watch one person at night to see who visits them. Ignores detection immunity.'),
    'mayor' : ('Mayor', 'Town Support',
        'Gain 3 votes when you reveal yourself as Mayor. Once revealed you cannot be healed by a Doctor.'),
    'medium' : ('Medium', 'Town Support',
        'Speak with all dead people (anonymously) at night. If dead, you can choose one living person during the day and speak to them that night. (Some caveats, see wiki)'),
    'retributionist' : ('Retributionist', 'Town Support',
        'You may revive a dead town aligned member (no Mafia/neutral). Cannot revive people who have left the game. The town will get a message when your target is revived.'),
    'sheriff' : ('Sheriff', 'Town Investigative',
        'Check one person each night for suspicious activity. You will know if your target is Mafia or a Serial Killer. Cannot deduce detect-immune roles (Godfather, Arsonist).'),
    'spy' : ('Spy', 'Town Investigative',
        'Listen in on the Mafia at night, and hear whispers. You will know who the Mafia visit at night. Retains spy abilities while dead.'),
    'transporter' : ('Transporter', 'Town Support',
        'Choose two people to transport at night. You can transport yourself. Targets will know if they are swapped. Immune to Witch\'s control.'),
    'veteran' : ('Veteran', 'Town Killing',
        'Decide if you will go on alert and kill anyone who visits you. You are invunerable while alert at night. Cannot be roleblocked. '+
        'You have 3 alerts. Doctors can save attackers. Being transported kills the Transporter but the swap still happens.'),
    'vigilante' : ('Vigilante', 'Town Killing',
        'Choose to take justice into your own hands and shoot someone. You have three shots. Cannot shoot the first night. '+
        'If you shoot a town aligned player you will commit sudoku from guilt. Cannot kill Night Immune players.')}

salem_mafia = {
    'blackmailer' : ('Blackmailer', 'Mafia Support',
        'Choose one person each night to blackmail. Target cannot talk during the day. During Judgement, blackmailed target\'s message will be changed to "I am blackmailed."'),
    'consigliere' : ('Consigliere', 'Mafia Support',
        'Check one person for their exact role each night. You will get their exact role, unlike the sheriff.'),
    'consort' : ('Consort', 'Mafia Support',
        'Distract someone each night. Prevents them from acting. You are immune to roleblocking. If you target a Serial Killer they will attack you instead.'),
    'disguiser' : ('Disguiser', 'Mafia Deception',
        'Choose a dying target to disguise yourself as. If your target dies you swap names, houses, and avatars. You only have 3 disguises.'),
    'framer' : ('Framer', 'Mafia Deception',
        'Choose one person to frame each night. Investigators will see framed targets as Framer. Sheriffs will see framed targets as Mafia.'),
    'godfather' : ('Godfather', 'Mafia Killing',
        'Kill someone each night. You can\'t be killed at night. You will appear to be a town member to the Sheriff. If you do not designate a target, the Mafioso may target anyone.'),
    'janitor' : ('Janitor', 'Mafia Deception',
        'Choose a dying person to clean each night. If your target dies at night their role and last will not be shown to the town, and only you will see them. You only have 3 cleanings.'),
    'mafioso' : ('Mafioso', 'Mafia Killing',
        'Carry out the Godfather\'s orders. If the Godfather designates a target, you will kill them. If Godfather is dead or did not choose to kill someone you can kill whoever you want. ')}

salem_neutrals = {
    'amnesiac' : ('Amnesiac', 'Neutral Benign',
        'Remember who you were by selecting a graveyard role. Choosing a role reveals it to the town. You can select a role cleaned by a Janitor, '+
        'but you cannot select a Unique role (Godfather, Mayor, etc...). You win if you complete your role\' goal or surivive to the end.'),
    'arsonist' : ('Arsonist', 'Neutral Killing',
        'Douse someone in gasoline or ignite all doused targets. Targets will know they are doused in gasoline. If you don\'t act at night you will clean yourself of gas. '+
        'Death from fire can\'t be prevented by healing or night immunities. You cannot affect jailed targets. Try not to light yourself on fire.'),
    'executioner' : ('Executioner', 'Neutral Evil',
        'Trick the Town into lynching your target. Your target is always a Town member. If your target is killed at night you will become a Jester that morning. '+
        'You cannot be killed at night (retained after target dies, but lost if you turn into a Jester). You win if your target is lynched (while you\'re alive?) before the game ends.'),
    'jester' : ('Jester', 'Neutral Evil',
        'Trick the Town into lynching you. If you are lynched, you may kill one of the GUILTY voters the following night. '+
        'This goes through any night immunity, however a transporter can swap your target with somebody else and get them killed instead.'),
    'serial killer' : ('Serial Killer', 'Neutral Killing',
        'Kill someone each night. If you are role blocked you will attack the blocker instead (Escort, Consort, and Jailor). You can not be killed at night.'),
    'survivor' : ('Survivor', 'Neutral Benign',
        'Put on a bulletproof vest at night, protecting yourself from attacks. You can only use the bulletproof vest 4 times. '+
        'Your vest will be destroyed regardless if you are attacked or not. You cannot protect yourself from the Arsonist\'s ignite, Jailor\'s execution, or Jester\'s haunt.'),
    'witch' : ('Witch', 'Neutral Evil',
        'Control someone each night. You can only control targetable actions such as detection and killing. You can force people to target themselves. '+
        'Your victim will know they are being controlled. You are immune to roleblocking. You win if you live to see the town lose.'),
    'werewolf' : ('Werewolf', 'Neutral Killing',
        'Every Full Moon, transform into a werewolf.  You can target a player\'s home, killing the occupant and anyone who visits, '+
        'or you can stay at home and kill anyone who visits you. Your attack ignores Night Immunity. Mechanically, you function almost identically to '+
        'the Serial Killer. You cannot attack yourself.')

    }

salem_roles = dict(salem_townies.items() + salem_mafia.items() + salem_neutrals.items())

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

    coms.append(command.SimpleCommand('#!dbsize', "We've got %s word pairs." % markov.redis_conn.dbsize(), bot, groups=me_only_group, prependuser=False))

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
        return ' '.join(args)
    coms.append(command.Command('#!echo', f, bot, groups=me_only_group))

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

    coms.append(command.Command('!uptime', f, bot, chanblacklist = ['mynameisamanda', 'gixgaming'], repeatdelay=15))


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

        return '[MMR function currently broken thanks valve]'

        if channel in dota.enabled_channels.keys() and not dota.enabled_channels[channel][1]:
            if user == channel:
                rs = '''Hi %s, I can provide accurate MMR and automatically announce \
                games when they are finished with mmr change and totals.  \
                All that is required is that you add me on steam and that your dota profile isn't private.  \
                Type "!mmrsetup" to get started (broadcaster only command).''' % channel
                return rs
            else:
                return

        isupdate = args and args[0].lower() == 'update' and bot.user_is_op(user) | {'imayhaveborkedit'}

        if args and 'update' in args[0].lower() and not isupdate:
            outputstring = "Solo: %s | Party: %s  (Did not update, you're not a mod!)"
        else:
            outputstring = "Solo: %s | Party: %s"

        if isupdate:
            print "Updating mmr"

            olddotadata = dota.getUserDotaData(channel)

            wentok = dota.updateMMR(channel)

            dotadata = dota.getUserDotaData(channel)

            old_mmr_s = str(olddotadata['game_account_client']['solo_competitive_rank'] or 0)
            old_mmr_p = str(olddotadata['game_account_client']['competitive_rank'] or 0)

            new_mmr_s = str(dotadata['game_account_client']['solo_competitive_rank'] or 0)
            new_mmr_p = str(dotadata['game_account_client']['competitive_rank'] or 0)

            mmr_s_change = str(int(new_mmr_s) - int(old_mmr_s))
            mmr_p_change = str(int(new_mmr_p) - int(old_mmr_p))

            if new_mmr_s == 0: new_mmr_s = 'None'
            if new_mmr_p == 0: new_mmr_p = 'None'

            if int(mmr_s_change) != 0: 
                mmr_s_change = ' (%s%s)' % ('+' if int(mmr_s_change) > 0 else '', mmr_s_change)
            else:
                mmr_s_change = ''
            
            if int(mmr_p_change) != 0: 
                mmr_p_change = ' (%s%s)' % ('+' if int(mmr_p_change) > 0 else '', mmr_p_change)
            else:
                mmr_p_change = ''

            return outputstring % ('%s%s' % (new_mmr_s, mmr_s_change), '%s%s' % (new_mmr_p, mmr_p_change))

        else:
            dotadata = dota.getUserDotaData(channel)

            try:
                mmr = dotadata['game_account_client']['solo_competitive_rank']
                mmrp = dotadata['game_account_client']['competitive_rank']
            except:
                print '[Dota-MMR] Error getting mmr fields for %s, might be first time setup' % channel
                wentok = dota.updateMMR(channel)
                dotadata = dota.getUserDotaData(channel)

                mmr = dotadata['game_account_client']['solo_competitive_rank']
                mmrp = dotadata['game_account_client']['competitive_rank']

            # ???
            return outputstring % (mmr,mmrp)

    coms.append(command.Command('!mmr', f, bot, repeatdelay=20))

    def f(channel, user, message, args, data, bot): #TODO: rework this since the bot can't add people
        import dota, node, settings
        '''
        76561197960265728 <- THAT IS THE NUMBER TO SUBTRACT FROM STEAM ID'S TO MAKE A DOTA ID

        I need to figure out what happens when you try to get a non friend mmr, catch that, and whatever else afterwards.
        '''

        if args:
            if args[0].lower() == 'help':
                helpstr = '!mmrsetup addme < steamid/profile link/profile name > -> Has the bot attempt to add you on steam from the provided steamid or profile link | '
                helpstr += '!mmrsetup addyou -> Returns a community link and a steam uri (for use with the Run dialog, Windows + r) to add the bot on steam from either one. '
                helpstr += 'Help arguments are also available for both commands. (!mmrsetup addme help)'
                return helpstr

            if args[0].lower() == 'addme':
                try:
                    if args[1].lower() == 'help':
                        return 'Usage: !mmrsetup addme < help | steamid | steam profile link >'
                except: return 'Usage: !mmrsetup addme < help | steamid | steam profile link >'

                steamid = dota.determineSteamid(args[1])

                if str(steamid) in node.raw_eval('bot.friends').keys():
                    return "You are already on the bot's friend list.  If you want to change something, use !dotaconfig"

                node.add_pending_mmr_enable(steamid, channel)
                node.add_friend(steamid)

                return "A friend request has been sent.  The steam bot will message you when you accept."


            if args[0].lower() == 'addyou':
                try:
                    if args[1].lower() == 'help':
                        return 'Usage: !mmrsetup addyou'
                except: pass

                outputstring = "I await your friend request and message (enable mmr channel_name).  "
                outputstring += "https://steamcommunity.com/id/Borkedbot/ or Run (Windows + r) -> steam://friends/add/76561198153108180"

                return outputstring
                # "When you add me, send me the following as a message through steam: verifytwitch %s" % channel
                # NODEJS REPLY TO MESSAGE: "To finish verification: say the following message in twitch chat: !mmrsetup verify {code}"

            if args[0].lower() == 'verify':
                if user not in [channel, 'imayhaveborkedit']:
                    return

                try:
                    args[1]
                except:
                    return "I need the code from the steam message."

                # if args[1].lower() == 'help':
                    # return 'blah blah help'

                if user == 'imayhaveborkedit':
                    verified = dota.determineSteamid(args[1])
                else:
                    verified = node.verify_code(channel, args[1].lower())

                if verified:
                    node.delete_key(channel)

                    en_chans = settings.getdata('dota_enabled_channels')
                    if channel in en_chans:
                        try:
                            if settings.getdata('%s_mmr_enabled' % channel):
                                return "Wtf you're already enabled.  If you want to change something use !dotaconfig"
                        except:
                            pass

                    settings.setdata('dota_enabled_channels', en_chans + [channel])
                    settings.trygetset('%s_common_name' % channel, channel)
                    settings.setdata('%s_mmr_enabled' % channel, True)

                    settings.setdata('%s' % channel, verified, domain='steamids')
                    settings.setdata('%s_dota_id' % channel, dota.steamToDota(verified))

                    node.remove_pending_mmr_enable(verified)

                    dota.update_channels()
                    dota.updateMMR(channel)

                    return "You did it!  Thanks for using this feature.  If you encounter any bugs or issues, let imayhaveborkedit know."
                else:
                    return "Bad code."



            # if args[0].lower() == 'setname' and len(args) >= 2 and user in [channel, 'imayhaveborkedit']:
            #     newname = ' '.join(args[1:])

            #     try:
            #         oldname = settings.getdata('%s_common_name' % channel)
            #     except:
            #         oldname = channel

            #     settings.setdata('%s_common_name' % channel, newname)
            #     dota.update_channels()

            #     return "Set common name for %s: %s -> %s" % (channel, oldname, newname)


            # if args[0].lower() == 'deletekey' and user == 'imayhaveborkedit':
            #     node.delete_key(channel)

            #     return "Deleted key for %s" % channel

            return "Bad option"

                # maybe change to simple explainations and say use the help argument
        return '''Hi.  Add the bot on steam and send it a steam message saying this: enable mmr'''

    coms.append(command.Command('!mmrsetup', f, bot, groups=me_and_broadcaster, repeatdelay=5))
    #TODO: Maybe split mmr setup stuff and configuration stuff

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
        deletekey (special)
        enable <dota | mmr>
        disable <dota | mmr>
        '''
        import settings, dota, node
        if args:

            if args[0].lower() == 'status':
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

                elif args[1] == 'mmr':
                    try:
                        settings.getdata('%s_dota_id' % channel)
                    except:
                        return "No dota id on record for %s, please use !mmrsetup" % channel
                    else:
                        settings.setdata('%s_mmr_enabled' % channel, True)


            if args[0].lower() == 'disable' and len(args) >= 2:
                if args[1] == 'dota':
                    dec = settings.getdata('dota_enabled_channels')
                    if channel not in dec:
                        return "Channel not enabled"

                    dec.remove(channel)
                    settings.setdata('dota_enabled_channels', dec)
                    dota.update_channels()

                elif args[1] == 'mmr':
                    settings.setdata('%s_mmr_enabled' % channel, False)


            if args[0].lower() == 'deletekey' and user == 'imayhaveborkedit':
                node.delete_key(channel)

                return "Deleted key for %s" % channel

    coms.append(command.Command('!dotaconfig', f, bot, groups=me_and_broadcaster, repeatdelay=5))

    def f(channel, user, message, args, data, bot):
        return "Currently broken due to Source 2.  Will be fixed Soon™."

        import dota, settings, node

        if channel not in dota.enabled_channels:
            return

        if user == 'bluepowervan' and not bot.user_is_op(user):
            bot.botsay('.timeout bluepowervan 3840')
            return "You know that doesn't work for you, stop trying."

        if not bot.user_is_op(user) and user != 'imayhaveborkedit':
            return

        if args:
            pages = int(args[0])
        else:
            pages = 33

        playerid = settings.getdata('%s_dota_id' % channel)

        if node.get_user_status(dota.dotaToSteam(playerid)) == '#DOTA_RP_PLAYING_AS':
            playerheroid = dota.getHeroIddict(False)[node.get_user_playing_as(dota.dotaToSteam(playerid))[0]]
        else:
            playerheroid = None

        if pages > 17 and playerheroid: pages = 17
        players = dota.searchForNotablePlayers(playerid, pages, playerheroid)

        if players is None:
            return "Game not found in %s pages." % pages

        if players:
            return "Notable players in this game: %s" % ', '.join(['%s (%s)' % (p,h) for p,h in players])
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
        if channel not in ['monkeys_forever', 'moodota2']: return

        namemap = {
            'monkeys_forever': 'monkeys-forever',
            'moodota2': 'Moo',
            'gixgaming': 'giX'
        }

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

    coms.append(command.Command(['!leaderboard', '!leaderboards'], f, bot, repeatdelay=25))

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
        import twitchapi
        if user not in bot.channelsubs:
            print user, 'is not a sub'
            if user != 'imayhaveborkedit' or not bot.user_is_op(user):
                return

        # return "please wait, bugs are being fixed"
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

    coms.append(command.SimpleCommand('!background',
        "It's a bug with the TI2 animated background.  Launch option: \"-dashboard international_2012\" "+
        "Console command: \"dota_embers 0\"  Then close, open, and close your console, and play a game.",
        bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand(['!fountainhooks', '!pudgefail', '!pudgefails'], 'rip root http://www.youtube.com/watch?v=7ba9nCot71w&hd=1',
        bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    # Barny #########################################################

    coms.append(command.SimpleCommand('!rightclick', 'dota_player_auto_repeat_right_mouse 1',
        bot, channels=['barnyyy'], targeted=True, repeatdelay=15))

    coms.append(command.SimpleCommand('!vectorpathing', 'dota_unit_allow_moveto_direction 1',
        bot, channels=['barnyyy'], targeted=True, repeatdelay=15))

    coms.append(command.SimpleCommand('!consolecommands', 'Right click mouse spam: dota_player_auto_repeat_right_mouse 1 -- No pathing movement: dota_unit_allow_moveto_direction 1',
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
        "Superjoe's vault of broken promises and intangible dreams.", "Superjoe's corn field."]

        random.shuffle(places)

        return 'It is currently %s in %s' % (time.asctime(), random.choice(places))

    coms.append(command.Command('!time', f, bot, channels=['superjoe'], repeatdelay=15))

    def f(channel, user, message, args, data, bot):
        try:
            args[0]
        except:
            return '%s: You need to give me a name!  Please type !registersalem salemusername' % user

        if user == 'superjoe':
            return "Come on superjoe, everyone knows who you are."
        elif user == 'imayhaveborkedit' and len(args) == 2:
            user = args[1]

        import cPickle, time
        username = args[0].replace('"', '')

        # Load names
        nameDB = None
        with open('/var/www/twitch/superjoe/salem/namemap', 'rb') as ndb:
            nameDB = cPickle.load(ndb)
            nameDB[user] = username

        # Load subs
        sublist = []
        with open('/var/www/twitch/superjoe/salem/subs', 'rb') as sl:
            sublist = cPickle.load(sl)
            sublist.extend(bot.channelsubs)
            sublist = list(set(sublist))

        # Easy way to empty a file
        open('/var/www/twitch/superjoe/salem/index.html', 'w').close()

        # Rewrite the file
        with open('/var/www/twitch/superjoe/salem/index.html', 'r+') as fi:
            fi.write('<html>\n<link rel="stylesheet" type="text/css" href="main.css">\n<body>\n')
            fi.write("<h1>Superjoe Town of Salem chat names</h1>\n<h5>Last update: %s</h5>\n\n" % time.asctime())

            fi.write("<p>Name Format:<br />Twitch name: Salem name</p>\n")
            fi.write("<p>superjoe: SuperJoe</p>\n\n")

            normals = []
            subs = []

            for u in nameDB.keys():
                (subs if u in sublist else normals).append(u)

            fi.write('<h2>Subs (%s)</h2>\n' % len(subs))
            fi.write('<ul>\n')

            for d in sorted(subs):
                if bot.usercolors.has_key(d):
                    fi.write('<li><b><span style="color:%s">%s</span></b>: %s</li>\n' % (bot.usercolors[d], d, nameDB[d]))
                else:
                    fi.write('<li>%s: %s</li>\n' % (d, nameDB[d]))

            fi.write('\n</ul>\n\n')

            fi.write('<h2>Non-Subs (%s)</h2>\n' % len(normals))

            for d in sorted(normals):
                # fi.write('<li>%s: %s</li>\n'%(d, nameDB[d]))
                if bot.usercolors.has_key(d):
                    fi.write('<li><b><span style="color:%s">%s</span></b>: %s</li>\n' % (bot.usercolors[d], d, nameDB[d]))
                else:
                    fi.write('<li>%s: %s</li>\n' % (d, nameDB[d]))

            fi.write('\n</ul>\n')

            fi.write("</body></html>")

        with open('/var/www/twitch/superjoe/salem/namemap', 'wb') as fi2:
            cPickle.dump(nameDB, fi2)

        with open('/var/www/twitch/superjoe/salem/subs', 'wb') as sl:
            cPickle.dump(sublist, sl)

        return "\"%s\" registered for %s" % (username, user)

    coms.append(command.Command('!registersalem', f, bot, channels=['superjoe'], groups=['salem']))

    def f(channel, user, message, args, data, bot):
        import cPickle, time

        try: username = args[0]
        except: username = None

        remname = None
        nameDB = None
        sublist = []

        with open('/var/www/twitch/superjoe/salem/namemap', 'rb') as ndb:
            nameDB = cPickle.load(ndb)
            remname = nameDB.pop(username, None)

        with open('/var/www/twitch/superjoe/salem/subs', 'rb') as sl:
            sublist = cPickle.load(sl)
            sublist.extend(bot.channelsubs)
            sublist = list(set(sublist))

        open('/var/www/twitch/superjoe/salem/index.html', 'w').close()

        with open('/var/www/twitch/superjoe/salem/index.html', 'r+') as fi:
            fi.write('<html>\n<link rel="stylesheet" type="text/css" href="main.css">\n<body>\n')
            fi.write("<h1>Superjoe Town of Salem chat names</h1>\n<h5>Last update: %s</h5>\n\n" % time.asctime())

            fi.write("<p>Name Format:<br />Twitch name: Salem name</p>\n")
            fi.write("<p>superjoe: SuperJoe</p>\n\n")

            normals = []
            subs = []

            for u in nameDB.keys():
                (subs if u in sublist else normals).append(u)

            fi.write('<h2>Subs (%s)</h2>\n' % len(subs))
            fi.write('<ul>\n')

            for d in sorted(subs):
                # fi.write('<li>%s: %s</li>\n' % (d, nameDB[d]))
                if bot.usercolors.has_key(d):
                    fi.write('<li><b><span style="color:%s">%s</span></b>: %s</li>\n' % (bot.usercolors[d], d, nameDB[d]))
                else:
                    fi.write('<li>%s: %s</li>\n' % (d, nameDB[d]))

            fi.write('\n</ul>\n\n')

            fi.write('<h2>Non-Subs (%s)</h2>\n' % len(normals))

            for d in sorted(normals):
                # fi.write('<li>%s: %s</li>\n'%(d, nameDB[d]))
                if bot.usercolors.has_key(d):
                    fi.write('<li><b><span style="color:%s">%s</span></b>: %s</li>\n' % (bot.usercolors[d], d, nameDB[d]))
                else:
                    fi.write('<li>%s: %s</li>\n' % (d, nameDB[d]))

            fi.write('\n</ul>\n')

            fi.write("</body></html>")

        with open('/var/www/twitch/superjoe/salem/namemap', 'wb') as fi2:
            cPickle.dump(nameDB, fi2)

        with open('/var/www/twitch/superjoe/salem/subs', 'wb') as sl:
            cPickle.dump(sublist, sl)

        if remname: return "Removed %s from name list." % username
        else: return "%s not found." % username

    coms.append(command.Command('#!unregistersalem', f, bot, True, channels=['superjoe'], groups=['salem']))

    ## Salem role curses

    # Medium

    def f(channel, user, message, args, data, bot):
        import settings
        cursecount = int(settings.trygetset('superjoe_mediums_curse', 0))
        cursestring = "Oh noes!  The medium has died %s times on night 1."

        if bot.user_is_op(user):
            try:
                if args:
                    watdo = args[0][0]
                    if watdo in ['+','-']:
                        cursecount += int(args[0][1:])
                    else:
                        cursecount = int(args[0][1:])
            except: pass
            else:
                settings.setdata('superjoe_mediums_curse', cursecount)
        elif args:
            cursestring += '  (Only mods can change the count)'

        return cursestring % cursecount

    coms.append(command.Command(['!mediumscurse', '!mediumcurse'], f, bot, channels=['superjoe'], groups=['salem'], repeatdelay=10))

    # Escort

    def f(channel, user, message, args, data, bot):
        import settings
        cursecount = int(settings.trygetset('superjoe_escorts_curse', 0))
        cursestring = "Oh noes!  The Escort has found the Serial Killer on the first night %s times."

        if bot.user_is_op(user):
            try:
                if args:
                    watdo = args[0][0]
                    if watdo in ['+','-']:
                        cursecount += int(args[0])
                    else:
                        cursecount = int(args[0])
            except: pass
            else:
                settings.setdata('superjoe_escorts_curse', cursecount)
        elif args:
            cursestring += '  (Only mods can change the count)'

        return  cursestring % cursecount
    coms.append(command.Command(['!escortscurse', '!escortcurse'], f, bot, channels=['superjoe'], groups=['salem'], repeatdelay=10))

    ####################

    coms.append(command.SimpleCommand(['!salem', '!salemhelp', '!saleminfo'],
        "Play Town of Salem here: http://www.blankmediagames.com/TownOfSalem/ Make an account, "+
        "add 'SuperJoe' as a friend, and type \"!registersalem accountname\" here in chat.  "+
        "Registering in chat isn't required but it helps Superjoe keep track of who's who.  "+
        "Subs get priority but everyone else gets invited afterwards.",
        bot, channels=['superjoe'], groups=['salem'], repeatdelay=6, prependuser=False, targeted=True))

    coms.append(command.SimpleCommand('!salemnames', 'http://doc.asdfxyz.de:81/twitch/superjoe/salem/',
        bot, channels=['superjoe'], groups=['salem'], repeatdelay=8, targeted=True))

    def f(channel, user, message, args, data, bot):
        if not len(args) or 'wiki' in args[0]:
            return "%s: http://town-of-salem.wikia.com/wiki/Roles" % user

        import difflib

        searchterm = difflib.get_close_matches(args[0].lower(), data.keys(), 1)

        if searchterm:
            return "%s (%s): %s" % data[searchterm[0].lower()]
        else:
            return "No match for \"%s\"" % args[0]

    coms.append(command.Command(['!salemrole', '!salemroles'], f, bot, channels=['superjoe'], data=salem_roles, groups=['salem'], repeatdelay=4))

    # Kizzmett ##########

    # Tom ##############

    coms.append(command.SimpleCommand('!plugs', 'Links! http://www.facebook.com/unsanitylive | http://twitter.com/unsanitylive | ' +
        'Like/Follow/Subscribe/whatever you want, that\'s where you can find Tom!',
        bot, channels=['unsanitylive'], prependuser=False, repeatdelay=10))

    # Moo

    coms.append(command.SimpleCommand('!ohnohesretarded', 'http://i.imgur.com/ZdaV0PG.png', bot, channels=['moodota2', 'barnyyy', 'lamperkat'], targeted=True, repeatdelay=15))

    coms.append(command.SimpleCommand('!announcer', 'Weeaboo Onodera+Kongou waifu announcer > http://saylith.github.io/harem-announcer/',
       bot, channels=['moodota2'], targeted=True, repeatdelay=15))

    #

    ######################################################################
    #
    # Test commands
    #

    def f(channel, user, message, args, data, bot):
        return "I don't think this command actually works, figure out how to do it properly."
        import dota, settings
        try:
            ccom = dota.get_console_connect_code(settings.getdata('%s_dota_id' % channel))
        except:
            return "Game not found (or some other error)"
        return 'Console command (Might result in a Bad relay password error, working on that): ' + ccom

    coms.append(command.Command('!watchgame', f, bot, groups=me_only_group))

    def f(channel, user, message, args, data, bot):
        import dota, settings, makegist

        pdata = dota.get_players_in_game_for_player(settings.getdata('%s_dota_id' % channel), checktwitch=True, markdown=True)

        if pdata is None:
            return 'Cannot find match.'

        addr = makegist.create_dota_playerinfo(channel, pdata, shorten=True)
        return "Player info for this game is available here: %s" % addr

    coms.append(command.Command('!playerinfo', f, bot, repeatdelay=30, groups=me_and_broadcaster))


    def f(channel, user, message, args, data, bot):
        import time

        if not args:
            return "You know you're supposed to give me names to unban right?"

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


#    def f(channel, user, message, args, data, bot):
#        import steamapi
#        data = steamapi.GetTournamentPrizePool(2733)
#
#        moneys = data['result']['prize_pool']
#
#        prizes = {
#            1600001: 'Valve fixes their shit',
#            100000000: 'Half Life 3 Released'
#        }
#
#        remaining = None
#        for prize in sorted(prizes.keys()):
#            if moneys < prize:
#                nextprize = prizes[prize]
#                remaining = prize - moneys
#                break
#
#        if moneys == 1600000:
#            remaining = False
#            nextprize = 'Valve pls fix ur shit'
#
#        if remaining:
#            return 'Current TI5 prize pool: ${:,} -- {} in ${:,}'.format(moneys, nextprize, remaining)
#        else:
#            return 'Current TI5 prize pool: ${:,} -- {}'.format(moneys, nextprize)
#
#    coms.append(command.Command('!prizepool', f, bot, True, repeatdelay=30))


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

            return "[Not sure if accurate] %s has followed %s for %s." % (followinguser, targetuser, ', '.join(timedata))

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


    ######################################################################

    message_commands = coms

    return "Generated %s message commands" % len(message_commands)


def _getargs(msg):
    try:
        a = msg.split()
    except:
        return list()
    if len(a) == 1:
        return list()
    else:
        return a[1:]