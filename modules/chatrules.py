# -*- coding: utf-8 -*-

import sys, os
import time, random, re, redis
import markov
import command, chatlogger
from command import get_process_output

import sys, math


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
    'bodyguard' : ('Bodyguard', 'Town Protective', 'Protect one person from death each night.'),
    'doctor' : ('Doctor', 'Town Protective', 'Heal one person each night, preventing them from dying.'),
    'escort' : ('Escort', 'Town Support', 'Distract someone each night.'),
    'investigator' : ('Investigator', 'Town Investigative', 'Investigate one person each night for a clue to their role.'),
    'jailor' : ('Jailor', 'Town Killing', 'You may choose one person during the day to jail for the night.'),
    'lookout' : ('Lookout', 'Town Investigative', 'Watch one person at night to see who visits them.'),
    'mayor' : ('Mayor', 'Town Support', 'Gain 3 votes when you reveal yourself as Mayor.'),
    'medium' : ('Medium', 'Town Support', 'Speak with all dead people at night.'),
    'retributionist' : ('Retributionist', 'Town Support', 'You may revive a dead town member.'),
    'sheriff' : ('Sheriff', 'Town Investigative', 'Check one person each night for suspicious activity.'),
    'spy' : ('Spy', 'Town Investigative', 'Listen in on the Mafia at night, and hear whispers.'),
    'transporter' : ('Transporter', 'Town Support', 'Choose two people to transport at night.'),
    'veteran' : ('Veteran', 'Town Killing', 'Decide if you will go on alert and kill anyone who visits you.'),
    'vigilante' : ('Vigilante', 'Town Killing', 'Choose to take justice into your own hands and shoot someone.')}

salem_mafia = {
    'blackmailer' : ('Blackmailer', 'Mafia Support', 'Choose one person each night to blackmail.'),
    'consigliere' : ('Consigliere', 'Mafia Support', 'Check one person for their exact role each night.'),
    'consort' : ('Consort', 'Mafia Support', 'Distract someone each night.'),
    'disguiser' : ('Disguiser', 'Mafia Deception', 'Choose a dying target to disguise yourself as.'),
    'framer' : ('Framer', 'Mafia Deception', 'Choose one person to frame each night.'),
    'godfather' : ('Godfather', 'Mafia Killing', 'Kill someone each night.'),
    'janitor' : ('Janitor', 'Mafia Deception', 'Choose a dying person to clean each night.'),
    'mafioso' : ('Mafioso', 'Mafia Killing', 'Carry out the Godfather\'s orders.')}

salem_neutrals = {
    'amnesiac' : ('Amnesiac', 'Neutral Benign', 'Remember who you were by selecting a graveyard role.'),
    'arsonist' : ('Arsonist', 'Neutral Killing', 'Douse someone in gasoline or ignite all doused targets.'),
    'executioner' : ('Executioner', 'Neutral Evil', 'Trick the Town into lynching your target.'),
    'jester' : ('Jester', 'Neutral Evil', 'Trick the Town into voting against you.'),
    'serial Killer' : ('Serial Killer', 'Neutral Killing', 'Kill someone each night.'),
    'survivor' : ('Survivor', 'Neutral Benign', 'Put on a bulletproof vest at night, protecting yourself from attacks.'),
    'witch' : ('Witch', 'Neutral Evil', 'Control someone each night.')}

salem_roles = dict(salem_townies.items() + salem_mafia.items() + salem_neutrals.items())

message_commands = []
joinpart_commands = []


def setup(bot):
    reload(command)

    generate_message_commands(bot)
    generate_joinpart_commands(bot)


def alert(event):
    if event.etype == 'msg':
        for comm in message_commands:
            output = comm.process(event.channel, event.user, event.data, _getargs(event.data))
            if output[1] is command.OK:
                print "[Chatrules] Output for %s: %s" % (comm.trigger, output[0])
                event.bot.say(event.channel, output[0])

    if event.etype in ['join', 'part']:
        # not quite yet
        pass


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

    ######################################################################
    #
    # Mod message_commands
    #

    coms.append(command.SimpleCommand('Beep?', 'Boop!', bot, True, prependuser = False))
    
    #TODO: ADD LIST OF BURSDAY SONGS?
    coms.append(command.SimpleCommand('#!bursday', "Happy Bursday! http://www.youtube.com/watch?v=WCYzk67y_wc", bot, True))

    coms.append(command.SimpleCommand('#!riot', 'ヽ༼ຈل͜ຈ༽ﾉ', bot, True, prependuser = False))

    def f(channel, user, message, args, data, bot):
        if 'nightbot' in set(bot.oplist + bot.userlist):
            if 'nightbot' in bot.oplist and 'nightbot' not in bot.userlist:
                return "Nightbot is modded but not in the channel? O.o"
            elif 'nightbot' not in bot.oplist and 'nightbot' in bot.userlist:
                return "I think nightbot just got here."
            return "Nightbot should be here."
        else:
            return "Nightbot doesn't seem to be here."

    coms.append(command.Command('!nightbot', f, bot, True))
    
    def f(channel, user, message, args, data, bot):
        if not len(args): 
            return

        pag = args[0].lower()
        # lower args[0]

        if pag in set(bot.oplist + bot.userlist):
            if pag in bot.oplist and pag not in bot.userlist:
                return "%s is modded but not in the channel? O.o" % pag
            return "%s should be here." % pag
        else:
            return "%s doesn't seem to be here." % pag

    coms.append(command.Command('!paging', f, bot, True))

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
            # Might add a cooldown message

    coms.append(command.Command('!saysomething', f, bot, repeatdelay=30))

    def f(channel, user, message, args, data, bot):
        if message.endswith('?'):
            return "%s, %s"%(user, random.choice(data))

    coms.append(command.SimpleCommand('Borkedbot, ', f, bot, data=magic8ball))

    ######################################################################
    #
    # Channel spcifics
    #

    # Monkeys_forever ####

    def f(channel, user, message, args, data, bot):
        if user != 'sage1447':
            return '%s: Anywhere between 5.8k and 6k' % user

    coms.append(command.Command('!mmr', f, bot, channels=['monkeys_forever'], repeatdelay=10))

    coms.append(command.SimpleCommand(['!music', '!playlist', '!songlist'], 
        "Monkeys' playlist can be found here: http://grooveshark.com/playlist/Stream/81341599", bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand('!songrequest', 'This aint no nightbot stream', bot, channels=['monkeys_forever'], repeatdelay=10))

    coms.append(command.SimpleCommand(['!song', '!currentsong'], 'The name of the song is in the top left of the stream.  Open your eyeholes!', bot,
        channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand('!background', 
        "It's a bug with the TI2 animated background.  Put this in your launch options: -dashboard international_2012", bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    coms.append(command.SimpleCommand(['!rangefinder', '!greenarrow', '!green arrow'], "Here's the console command: dota_disable_range_finder 0", 
        bot, channels=['monkeys_forever'], repeatdelay=10, targeted=True))

    # Superjoe ####

    coms.append(command.SimpleCommand('!youtube', 'Subscribe to Superjoe on youtube!  https://www.youtube.com/user/WatchSuperjoe', bot, channels=['superjoe'], prependuser=False, targeted=True))
    coms.append(command.SimpleCommand('!twitter', 'Follow Superjoe on Twitter!  http://twitter.com/superjoeplays', bot, channels=['superjoe'], prependuser=False, targeted=True))
    
    coms.append(command.SimpleCommand('!ytmnd', 'http://superjoe.ytmnd.com (courtesy of Slayerx1177)', bot, channels=['superjoe'], prependuser=False, targeted=True))

    def f(channel, user, message, args, data, bot):
        try:
            args[0]
        except:
            return '%s: You need to give me a name!  Please type !registersalem salemusername' % user

        if user == 'superjoe':
            return "Come on superjoe, everyone knows who you are."

        import cPickle
        username = args[0].replace('"', '')
        nameDB = cPickle.load(open('/var/www/twitch/superjoe/salem/namemap', 'rb'))
        nameDB[user] = username

        open('/var/www/twitch/superjoe/salem/index.html', 'w').close()
        with open('/var/www/twitch/superjoe/salem/index.html', 'r+') as fi:
            fi.write("<html><pre>\n")
            fi.write("Superjoe Town of Salem chat names (sub indicator coming)\n\n")
            fi.write("Twitch name: Salem name\n\n")
            fi.write("superjoe: Superjoe\n\n")
            
            for d in sorted(nameDB.keys()):
                fi.write('%s: %s\n'%(d, nameDB[d]))
            fi.write("</pre></html>")

        with open('/var/www/twitch/superjoe/salem/namemap', 'wb') as fi2:
            cPickle.dump(nameDB, fi2)

        return "\"%s\" registered for %s" % (username, user)

    coms.append(command.Command('!registersalem', f, bot, channels=['superjoe'], groups=['salem']))

    coms.append(command.SimpleCommand(['!salem', '!salemhelp', '!saleminfo'], 
        "Play Town of Salem here: http://www.blankmediagames.com/TownOfSalem/ Make an account, "+
        "add 'SuperJoe' as a friend, and type \"!registersalem accountname\" here in chat. (Not needed but it helps)", 
        bot, channels=['superjoe'], groups=['salem'], repeatdelay=6, prependuser=False, targeted=True))

    coms.append(command.SimpleCommand('!salemnames', 'http://doc.asdfxyz.de:81/twitch/superjoe/salem/', 
        bot, channels=['superjoe'], groups=['salem'], repeatdelay=6, targeted=True))


    def f(channel, user, message, args, data, bot):
        if not len(args):
            return

        # TODO: add support for difflib matching
        for k in data.keys():
            if args[0].lower() in k:
                return "%s (%s): %s" % data[k]
    
        return "\"%s\" not found."
    
    coms.append(command.Command('!salemrole', f, bot, channels=['superjoe'], data=salem_roles, groups=['salem']))

    ######################################################################

    #coms.append(command.SimpleCommand('!argtest', 'This is the test', bot, prependuser = False, targeted=True))

    message_commands = coms

    return "Generated %s message commands" % len(message_commands)



def generate_joinpart_commands(bot):
    global joinpart_commands



def _getargs(msg):
    a = msg.split()
    if len(a) == 1:
        return list()
    else:
        return a[1:]