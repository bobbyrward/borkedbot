import sys
sys.dont_write_bytecode = True

import time, random
import settings, twitchapi

LOAD_ORDER = 200


def setup(bot):
    return

def alert(event):
    if event.channel != 'cosmowright' or event.bot.nickname not in event.bot.oplist:
        return

    last_powerup = settings.trygetset('cosmo_rng_last_powerup', time.time())
    rng_mode = settings.trygetset('cosmo_rng_mode', False)

    if last_powerup + 3600 <= time.time() and rng_mode:
        powerup(event.bot)

    if event.etype == 'msg':
        if user in settings.getdata('cosmo_rng_gods') and event.data.startswith('!timeout') and rng_mode:
            args = event.data.split()
            if len(args) == 3:
                t, who, duration = args
                try:
                    duration = int(duration)
                except: pass
                else:
                    maxto = settings.trygetset('cosmo_rng_maxto', 600)
                    event.bot.botsay('.timeout %s %s' % (who, duration if duration <= maxto else maxto))

def powerup(bot):
    if not twitchapi.is_streaming('cosmowright'):
        return

    chatters = twitchapi.get_chatters('cosmowright')['chatters']['viewers']

    new_powerups = int(len(chatters) * 0.05)
    new_gods = random.sample(chatters, new_powerups)

    settings.setdata('cosmo_rng_gods', new_gods)
    settings.setdata('cosmo_rng_last_powerup', time.time())

    bot.botsay("The RNG gods have spoken, their chosen are: " + ' ,'.join(new_gods))

def test():
    chatters = twitchapi.get_chatters('cosmowright')['chatters']['viewers']

    new_powerups = int(len(chatters) * 0.05)
    new_gods = random.sample(chatters, new_powerups)

    return "(test run) Chatters: %s, 5%% = %s, chosen: %s" % (len(chatters), new_powerups, ', '.join([str(g) for g in new_gods]))
