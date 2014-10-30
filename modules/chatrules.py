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
        'Your victim will know they are being controlled. You are immune to roleblocking. You win if you live to see the town lose.')}

salem_roles = dict(salem_townies.items() + salem_mafia.items() + salem_neutrals.items())

message_commands = []
joinpart_commands = []


def setup(bot):
    reload(command)

    generate_message_commands(bot)
    generate_joinpart_commands(bot)


def alert(event):
    if event.etype == 'msg':
        tstart = time.time()
        for comm in message_commands:
            t1 = time.time()
            output = comm.process(event.channel, event.user, event.data, _getargs(event.data))
            t2 = time.time()
            if output[1] is command.OK:
                print "[Chatrules] Output for %s: %s" % (comm.trigger, output[0])
                print "[Chatrules] Command time: %4.4fms, Total time: %4.4fms" % ((t2-t1)*1000, (t2-tstart)*1000)
                event.bot.say(event.channel, output[0])

    #if event.etype in ['join', 'part']:
    #    # not quite yet, maybe not for a while
    #    pass


def generate_message_commands(bot):
    # generate_special_commands()
    # generate_general_commands()
    # generate_channel_commands()
    global message_commands
    coms = []

    #print "Commands are being generated"


    #############################
    #
    # SPECIAL RESTRICTED message_COMMANDS
    #
    #############################

    me_only_group = ['special']
    me_and_host = ['special', 'broadcaster']

    coms.append(command.SimpleCommand('#!dbsize', "We've got %s entries." % markov.redis_conn.dbsize(), bot, groups=me_only_group, prependuser=False))

    _opstr = str(bot.oplist).replace('[','').replace(']', '').replace('\'','')
    _ostr = "There are %s mods in chat: %s" % (len(bot.oplist), _opstr)
    coms.append(command.SimpleCommand('#!ops', _ostr, bot, groups=me_only_group, prependuser=False))
    coms.append(command.SimpleCommand('#!opnum', "There are %s mods in chat" % len(bot.oplist), bot, groups=me_only_group, prependuser=False))

    # Exec #

    def f(channel, user, message, args, data, bot):
        print "Executing: %s" % message[7:]
        try:
            exec message[7:] in globals(), locals()
        except BaseException as e:
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
        except BaseException as e:
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


    ## Node related message_commands ##


    def f(channel, user, message, args, data, bot):
        import node

        if args:
            if args[0].lower() == 'status':
                con_steam, con_dota = node.status()

                status_steam = "Ok" if con_steam else "Not ok"
                status_dota = "Ok" if con_dota else "Not ok"

                return "Connection status: Steam: %s | Dota: %s" % (status_steam, status_dota)

            if args[0].lower() == 'restart':
                node.restart()

                return "Restarting steam bot, this should only take a few seconds."

            if args[0].lower() == 'matchmaking':
                import difflib, time
                mmdata = node.get_mm_stats()

                try:
                    args[1]
                except:
                    args.append('USEast')

                # region = difflib.get_close_matches(args[1], mmdata.keys(), 1)[0]

                try:
                    lnames = {n.lower():n for n in mmdata.keys()}
                    region = [lnames[r] for r in difflib.get_close_matches(args[1].lower(), lnames, 1)][0]
                except:
                    return "No match for %s" % args[1]

                waittimes, searchers = mmdata[region]

                return  "Matchmaking data for region %s: Average queue time: %s, In queue: %s" % (
                    region, time.strftime("%M:%S", time.gmtime(waittimes)), searchers)


    coms.append(command.Command('#!node', f, bot, groups=me_only_group))

    def f(channel, user, message, args, data, bot):
        import twitchapi, datetime, dateutil.parser, dateutil.relativedelta

        isotime = twitchapi.get('users/%s' % args[0], 'created_at')
        t_0 = dateutil.parser.parse(isotime)
        t_now = datetime.datetime.now(dateutil.tz.tzutc())
        reldelta = dateutil.relativedelta.relativedelta(t_now, t_0)
        reldelta.microseconds = 0

        return str(reldelta).replace('relativedelta','').replace('+','').replace('(','').replace(')','')

    coms.append(command.Command('#!accountage', f, bot, groups=me_only_group))

    ######################################################################
    # Broadcaster/me message_commands
    #

    def f(channel, user, message, args, data, bot):
        import random
        import node, settings
        from dota import Lobby

        # BLARGH SET UP ARGPARSE

        try:
            lobby = settings.getdata('latest_lobby')
        except:
            lobby = None

        # TODO: move options up here
        # parser.add_argument('option', choices=['create', 'leave', 'remake', 'start', 'shuffle', 'flip', 'kick'])

        if args:
            if args[0].lower() == 'create':
                if lobby:
                    return "A lobby already exists (%s)" % lobby.chanel

                import argparse
                options = args[1:]

                parser = argparse.ArgumentParser('create')
                pwgroup = parser.add_mutually_exclusive_group()

                #def __init__(self, channel, name=None, password=None, mode=None, region=None):
                parser.add_argument('-name', nargs='*', default='Borkedbot lobby', type=str)
                parser.add_argument('-mode', choices=Lobby.GAMEMODES.keys(), default='AP')
                parser.add_argument('-server', choices=Lobby.SERVERS.keys(), default='Auto', dest='region')
                pwgroup.add_argument('-password', nargs='*', default=argparse.SUPPRESS, type=str)
                pwgroup.add_argument('-randompassword', action='store_true', default=argparse.SUPPRESS) # ENHANCE with action or something

                try:
                    ns = parser.parse_args(options)
                except BaseException as e:
                    return "you did something wrong"

                prepasswordns = str(ns)

                if hasattr(ns, 'randompassword'):
                    ns.password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
                    del ns.randompassword

                print ns
                lobby = Lobby(channel, **vars(ns))
                lobby.create()
                settings.setdata('latest_lobby', lobby)
                return "A LOBBY HAS BEEN CREATED %s" % prepasswordns.replace('Namespace','')

            if args[0].lower() == 'leave':
                if lobby:
                    lobby.leave()
                    settings.deldata('latest_lobby')
                    return "Lobby has been abandoned."

            if args[0].lower() == 'remake':
                if lobby:
                    lobby.remake() #TODO: add options parsing

            if args[0].lower() == 'start':
                if lobby:
                    lobby.start()
                    lobby.leave()

            if args[0].lower() == 'shuffle':
                if lobby:
                    lobby.shuffle()

            if args[0].lower() == 'flip':
                if lobby:
                    lobby.flip()

            if args[0].lower() == 'kick':
                if lobby:
                    return 'Not yet implemented'


            if args[0].lower() == 'help':
                return "!lobby options: create, leave, remake, start, shuffle, flip, kick"
        else:
            if not lobby:
                return "No lobby"
            else:
                return "Current lobby: yes (%s)" % lobby.channel # TODO: add __repr__


    coms.append(command.Command('!lobby', f, bot, True))

    ######################################################################
    # Mod message_commands
    #

    coms.append(command.SimpleCommand('Beep?', 'Boop!', bot, True, prependuser = False))

    coms.append(command.SimpleCommand(['!source', '!guts'], "BLEUGH https://github.com/imayhaveborkedit/borkedbot", bot, True, prependuser=True, targeted=True))

    #TODO: ADD LIST OF BURSDAY SONGS?
    coms.append(command.SimpleCommand('#!bursday', "Happy Bursday! http://www.youtube.com/watch?v=WCYzk67y_wc", bot, True))

    coms.append(command.SimpleCommand('#!riot', 'ヽ༼ຈل͜ຈ༽ﾉ', bot, True, prependuser = False))
    coms.append(command.SimpleCommand('#!shrug', '¯\_(ツ)_/¯', bot, True, prependuser = False))

    #coms.append(command.SimpleCommand('#!subcount', '%s' % len(bot.channelsubs), bot, True))

    # def f(channel, user, message, args, data, bot):
    #     if 'nightbot' in set(bot.oplist + bot.userlist):
    #         if 'nightbot' in bot.oplist and 'nightbot' not in bot.userlist:
    #             return "Nightbot is modded but not in the channel? O.o"
    #         elif 'nightbot' not in bot.oplist and 'nightbot' in bot.userlist:
    #             return "I think nightbot just got here."
    #         return "Nightbot should be here."
    #     else:
    #         return "Nightbot doesn't seem to be here."

    # coms.append(command.Command('!nightbot', f, bot, True))

    # def f(channel, user, message, args, data, bot):
    #     if not len(args):
    #         return

    #     pag = args[0].lower()
    #     # lower args[0]

    #     if pag in set(bot.oplist + bot.userlist):
    #         if pag in bot.oplist and pag not in bot.userlist:
    #             return "%s is modded but not in the channel? O.o" % pag
    #         return "%s should be here." % pag
    #     else:
    #         return "%s doesn't seem to be here." % pag

    # coms.append(command.Command('!paging', f, bot, True))

    def f(channel, user, message, args, data, bot):
        return get_process_output('ddate', shell=True)
    coms.append(command.Command('#!ddate', f, bot, True))

    def f(channel, user, message, args, data, bot):
        while True:
            out = get_process_output('fortune', shell=True)
            if len(out) <= 256:
                return out

    coms.append(command.Command('#!fortune', f, bot, True))

    def f(channel, user, message, args, data, bot):
        while True:
            out = get_process_output('ofortune', shell=True)
            if len(out) <= 256:
                return out

    coms.append(command.Command('#!ofortune', f, bot, True))


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

    coms.append(command.Command('!saysomething', f, bot, repeatdelay=30))

    def f(channel, user, message, args, data, bot):
       if message.endswith('?'):
           return "%s, %s"%(user, random.choice(data))

    coms.append(command.Command('Borkedbot,', f, bot, chanblacklist=['monkeys_forever'], data=magic8ball))

    def f(channel, user, message, args, data, bot):
        import datetime, dateutil, dateutil.parser, dateutil.relativedelta, twitchapi, settings

        if user in ['jewishoverlord']:
            return

        if args:
            channel = args[0].lower()
        streamdata = twitchapi.get('streams/%s' % channel.replace('#',''), 'stream')

        day_str = "{0}, {1} has been streaming for approximately {2.days} days, {2.hours} hours and {2.minutes} minutes."
        hour_str = "{0}, {1} has been streaming for approximately {2.hours} hours and {2.minutes} minutes."

        if settings.getdata('%s_is_hosting' % channel) and not args:
            hc = settings.getdata('%s_hosted_channel' % channel)

            if hc and not args:
                streamdata = twitchapi.get('streams/%s' % hc, 'stream')
                channel = hc
                day_str += ' (hosted channel)'
                hour_str += ' (hosted channel)'

        if streamdata is None:
            return "There is no stream D:"

        isotime = streamdata['created_at']

        t_0 = dateutil.parser.parse(isotime)
        t_now = datetime.datetime.now(dateutil.tz.tzutc())

        reldelta = dateutil.relativedelta.relativedelta(t_now, t_0)

        if reldelta.days:
            return day_str.format(user, channel, reldelta)
        else:
            return hour_str.format(user, channel, reldelta)

    coms.append(command.Command('!uptime', f, bot, chanblacklist = ['mynameisamanda', 'siractionslacks'], repeatdelay=15))
    # TODO: Meh idiots

    def f(channel, user, message, args, data, bot):
        if args:
            if bot.usercolors.has_key(args[0].lower()):
                return bot.usercolors[args[0].lower()]
            else:
                return "No data for %s" % args[0].lower()
        else:
            return "Use the command properly, idiot."

    coms.append(command.Command('!usercolor', f, bot, True, repeatdelay=8))

    ######################################################################
    #
    # Channel spcifics
    #

    # Sort of general ######################################################

    def f(channel, user, message, args, data, bot):
        import json, os, time, settings, dota

        if channel not in dota.enabled_channels.keys():
            return

        if channel in dota.enabled_channels.keys() and not dota.enabled_channels[channel][1]:
            if user == channel:
                rs = '''Hi %s, I can provide accurate MMR and automatically announce ranked \
                games when they are finished with mmr change and totals.  \
                All that is required is that you add me on steam and that your dota profile isn't private.  \
                Type "!mmrsetup" to get started (broadcaster only command).''' % channel
                return rs
            else:
                return

        isupdate = args and args[0].lower() == 'update' and user in bot.oplist | {'imayhaveborkedit'}

        if args and 'update' in args[0].lower() and not isupdate:
            if user == 'gggccca7x':
                outputstring = "stfu gggccca7x"
            else:
                outputstring = "Solo: %s | Party: %s  (Did not update, you're not a mod!)"
        else:
            outputstring = "Solo: %s | Party: %s"

        if isupdate:
            print "Updating mmr"

            olddotadata = dota.getUserDotaData(channel)

            wentok = dota.updateMMR(channel)

            dotadata = dota.getUserDotaData(channel)

            old_mmr_s = str(olddotadata['gameAccountClient']['soloCompetitiveRank'])
            old_mmr_p = str(olddotadata['gameAccountClient']['competitiveRank'])

            new_mmr_s = str(dotadata['gameAccountClient']['soloCompetitiveRank'])
            new_mmr_p = str(dotadata['gameAccountClient']['competitiveRank'])

            mmr_s_change = str(int(new_mmr_s) - int(old_mmr_s))
            mmr_p_change = str(int(new_mmr_p) - int(old_mmr_p))

            if int(mmr_s_change) >= 0: mmr_s_change = '+' + mmr_s_change
            if int(mmr_p_change) >= 0: mmr_p_change = '+' + mmr_p_change

            return outputstring % ('%s (%s)' % (new_mmr_s, mmr_s_change), '%s (%s)' % (new_mmr_p, mmr_p_change))

        else:
            dotadata = dota.getUserDotaData(channel)

            mmr = dotadata['gameAccountClient']['soloCompetitiveRank']
            mmrp = dotadata['gameAccountClient']['competitiveRank']

            # ???
            return outputstring % (mmr,mmrp)

    coms.append(command.Command('!mmr', f, bot, repeatdelay=16))

    def f(channel, user, message, args, data, bot):
        import dota, node, settings
        '''


        mmmm    mmmm        mmmmmmm m    m mmmmm   mmmm
        #   "m m"  "m          #    #    #   #    #"   "
        #    # #    #          #    #mmmm#   #    "#mmm
        #    # #    #          #    #    #   #        "#
        #mmm"   #mm#           #    #    # mm#mm  "mmm#"



        76561197960265728 <- THAT IS THE NUMBER TO SUBTRACT FROM STEAM ID'S TO MAKE A DOTA ID

        Two options:
            !mmrsetup addme <link or id>
            !mmrsetup addyou

        addme:
            Parse link or id, add them as friend

        addyou:
            Link to steam profile and steam://friends/add/76561198153108180

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

                steamthing = args[1]
                steamid = ''

                if 'steamcommunity.com/id/' in steamthing or 'steamcommunity.com/profiles/' in steamthing:
                    steamid = [x for x in steamthing.split('/') if x][-1] # oh I hope this works
                else:
                    import re
                    match = re.match('^\d*$', steamthing)
                    if match:
                        steamid = match.string
                    else:
                        import steamapi
                        result = steamapi.ResolveVanityURL(steamthing)['response']
                        if result['success'] == 1:
                            steamid = result['message']
                        else:
                            return "Bad name, no match."

                print "Determined that %s's steamid is: %s" % (channel, steamid)

                if str(steamid) in node.raw_eval('bot.friends').keys():
                    return "You are already on the bot's friend list.  If you want to change something, use [commands I need to write]"

                node.add_friend(steamid)

                node.send_steam_message(steamid, "Twitch user '%s' has requested to enable mmr data for this account.  " % channel +
                    "If you have received this message in error, or have no idea what this is, simply ignore this message or block this bot.")

                node.send_steam_message(steamid, "To generate a verification code, please type this: enable mmr your_twitch_channel")

                

            if args[0].lower() == 'addyou':
                try:
                    if args[1].lower() == 'help':
                        return 'Usage: !mmrsetup addyou'
                except: pass

                return "I await your friend request and message (enable mmr).  https://steamcommunity.com/id/Borkedbot/ or Run (Windows + r) -> steam://friends/add/76561198153108180"

                # "When you add me, send me the following as a message through steam: verifytwitch %s" % channel
                # NODEJS REPLY TO MESSAGE: "To finish verification: say the following message in twitch chat: !mmrsetup verify {code}"

            if args[0].lower() == 'verify' and len(args) >= 2:
                if user not in [channel, 'imayhaveborkedit']:
                    return

                if args[1].lower() == 'help':
                    return 'blah blah help'

                verified = node.verify_code(channel, args[1].lower())

                if verified:
                    node.delete_key(channel)

                    en_chans = settings.getdata('dota_enabled_channels')
                    if channel in en_chans:
                        return "Wtf you're already enabled.  If you want to change something use [commands i need to write]"

                    settings.setdata('dota_enabled_channels', en_chans + [channel])
                    settings.trygetset('%s_common_name' % channel, channel)
                    settings.setdata('%s_mmr_enabled' % channel, True)

                    settings.setdata('%s', verified, domain='steamids')

                    dota.update_channels()
                    # set channel as enabled in settings

                    return "You did it!  Thanks for using this feature.  If you encounter any bugs or issues, let imayhaveborkedit know."
                else:
                    return "Bad code."


            if args[0].lower() == 'setname' and len(args) >= 2 and user in [channel, 'imayhaveborkedit']:
                newname = ' '.join(args[1:])

                try:
                    oldname = settings.getdata('%s_common_name' % channel)
                except:
                    oldname = channel

                settings.setdata('%s_common_name' % channel, newname)
                dota.update_channels()

                return "Set common name for %s: %s -> %s" % (channel, oldname, newname)


            if args[0].lower() == 'deletekey' and user == 'imayhaveborkedit':
                node.delete_key(channel)

                return "Deleted key for %s" % channel

            return "Bad option"

                # maybe change to simple explainations and say use the help argument
        return '''Hi.  You have two options.  1: You give me something to add you from (example: http://i.imgur.com/7Yepc8i.png either blue section or either link) \
                or 2: you add me on steam.  These are the commands, respectively: !mmrsetup addme < steam thing > OR !mmrsetup addyou.  \
                Once added, send me a message saying this: enable mmr'''

    coms.append(command.Command('!mmrsetup', f, bot, groups=['broadcaster'], repeatdelay=15))
    #TODO: Maybe split mmr setup stuff and configuration stuff

    coms.append(command.SimpleCommand('!mumble', 'doc.asdfxyz.de (default port) 100 slot open server, on 24/7.  Try not to be awful, or bork will ban you.',
        bot, channels=['superjoe', 'monkeys_forever'], repeatdelay=10, targeted=True))

    # Monkeys_forever ######################################################

    def f(channel, user, message, args, data, bot):
        import json, requests, time, datetime, dateutil, dateutil.tz, dateutil.relativedelta
        lburl = "http://www.dota2.com/webapi/ILeaderboard/GetDivisionLeaderboard/v0001?division=americas"
        jdata = json.loads(requests.get(lburl).text)

        rank, mmr = {i['name']:(i['rank'],i['solo_mmr']) for i in jdata['leaderboard']}['monkeys-forever']
        ltime = time.localtime(int(jdata['time_posted']))

        lastupdate = time.strftime('%b %d, %I:%M%p',ltime)
        lt = datetime.datetime.fromtimestamp(time.mktime(ltime)).replace(tzinfo=dateutil.tz.tzutc())
        t_now = datetime.datetime.now(dateutil.tz.tzutc())

        reldelta = dateutil.relativedelta.relativedelta(t_now, lt)

        daystr = ('Monkeys is rank {0} on the leaderboards, with {1} mmr. Last leaderboard update: '
            '{2.days} days, {2.hours} hours, {2.minutes} minutes ago ( http://dota2.com/leaderboards/#americas )')

        hourstr = ('Monkeys is rank {0} on the leaderboards, with {1} mmr. Last leaderboard update: '
            '{2.hours} hours, {2.minutes} minutes ago ( http://dota2.com/leaderboards/#americas )')

        minstr = ('Monkeys is rank {0} on the leaderboards, with {1} mmr. Last leaderboard update: '
            '{2.minutes} minutes ago ( http://dota2.com/leaderboards/#americas )')

        if reldelta.days:
            return daystr.format(rank, mmr, reldelta)
        elif reldelta.hours:
            return hourstr.format(rank, mmr, reldelta)
        else:
            return minstr.format(rank, mmr, reldelta)

    coms.append(command.Command(['!leaderboard', '!leaderboards'], f, bot, channels=['monkeys_forever'], repeatdelay=15))

    coms.append(command.SimpleCommand('!dotabuff', 'http://www.dotabuff.com/players/86811043 There you go.', bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand(['!music', '!playlist', '!songlist'],
        "Monkeys' playlist can be found here: http://grooveshark.com/playlist/Stream/81341599", bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand('!songrequest', 'This aint no nightbot stream', bot, channels=['monkeys_forever'], repeatdelay=10))

    coms.append(command.SimpleCommand(['!song', '!currentsong'], 'The name of the song is in the top left of the stream.  Open your eyeholes!', bot,
        channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand('!background',
        "It's a bug with the TI2 animated background.  Launch option: \"-dashboard international_2012\" "+
        "Console command: \"dota_embers 0\"  Then close, open, and close your console, and play a game.",
        bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand(['!rangefinder', '!greenarrow', '!green arrow'], "Here's the console command: dota_disable_range_finder 0",
        bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand(['!fountainhooks', '!pudgefail', '!pudgefails'], 'rip root http://www.youtube.com/watch?v=7ba9nCot71w&hd=1',
        bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    # Superjoe ######################################################

    coms.append(command.SimpleCommand('!youtube', 'Subscribe to Superjoe on youtube!  https://www.youtube.com/user/WatchSuperjoe',
        bot, channels=['superjoe'], prependuser=False, targeted=True, repeatdelay=8))

    coms.append(command.SimpleCommand('!twitter', 'Follow Superjoe on Twitter!  http://twitter.com/superjoeplays',
        bot, channels=['superjoe'], prependuser=False, targeted=True, repeatdelay=8))

    coms.append(command.SimpleCommand('!ytmnd', 'http://superjoe.ytmnd.com (courtesy of Slayerx1177)',
        bot, channels=['superjoe'], prependuser=False, targeted=True, repeatdelay=8))

    coms.append(command.SimpleCommand('!plugs', 'Youtube: https://youtube.com/user/WatchSuperjoe | Twitter: http://twitter.com/superjoeplays | ' +
        'Like/Follow/Subscribe/whatever you want, that\'s where you can find Superjoe!',
        bot, channels=['superjoe'], prependuser=False, targeted=True, repeatdelay=8))


    def f(channel, user, message, args, data, bot):
        import random
        places = ["Superjoe Land.", "Superjoe's dirty hovel.", "Superjoe's shining kingdom.", "Superjoe's murky swamp.", "Superjoe's haunted house.",
        "Superjoe's secret cave under monkeys_forever's house.", "Superjoe's bathtub.", "Superjoe's slave dungeon.", "Superjoe's deflated bouncy castle.",
        "Superjoe's vault of broken promises and intangible dreams.", "Superjoe's corn field."]

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

        if user in bot.oplist:
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

        if user in bot.oplist:
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

    # ???

    ######################################################################
    #
    # Test commands
    #

    ######################################################################

    message_commands = coms

    return "Generated %s message commands" % len(message_commands)


def generate_joinpart_commands(bot):
    global joinpart_commands


def _getargs(msg):
    try:
        a = msg.split()
    except:
        return list()
    if len(a) == 1:
        return list()
    else:
        return a[1:]