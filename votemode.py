import sopel
from sopel.module import OP, VOICE, require_privilege
from sopel.tools import Identifier
from math import floor
from datetime import datetime
from datetime import timedelta
from time import sleep

def clear_votes(bot):
    bot.memory['votes'] = {'kick': dict(),
                           'ban': dict(),
                           'voice': dict(),
                           'quiet': dict(),
                           'registered': list(),
                           'moderated': list()
                          }

def setup(bot):
    bot.cap_req('votemode', 'extended-join')
    bot.cap_req('votemode', 'account-notify')
    bot.memory['active_users'] = dict()
    bot.memory['quiet_users'] = dict()
    bot.memory['last_vote'] = datetime.now()
    bot.memory['mode_threshold'] = dict()
    bot.memory['mode_threshold']['kick'] = 0.5
    bot.memory['mode_threshold']['ban'] = 0.66
    bot.memory['mode_threshold']['moderated'] = 0.3
    bot.memory['mode_threshold']['registered'] = 0.4
    bot.memory['mode_threshold']['voice'] = 0.4
    bot.memory['mode_threshold']['quiet'] = 0.5
    bot.memory['vote_methods'] = {'kick': do_kick,
                                  'ban': do_ban,
                                  'voice': do_voice,
                                  'quiet': do_quiet,
                                  'registered': do_registered,
                                  'moderated': do_moderated
                                 }
    bot.memory['protected_timestamp'] = None
    clear_votes(bot)

def prune_active_users(bot):
    for channel in bot.memory['active_users']:
        to_prune = list()
        for user in bot.memory['active_users'][channel]:
            if bot.memory['active_users'][channel][user] + timedelta(minutes=15) < datetime.now():
                to_prune.append(user)
        for user in to_prune:
            del bot.memory['active_users'][channel][user]

def clear_protection(bot, channel):
    if bot.memory['protected_timestamp'] is None:
        return
    if bot.memory['protected_timestamp'] + timedelta(minutes=30) < datetime.now():
        bot.memory['protected_timestamp'] = None
        bot.write(['mode', channel, '-r'])
        bot.write(['mode', channel, '-m'])

#clear quiets and prune_active_users use the same logic and could just be a
#single function
def clear_quiets(bot):
    for channel in bot.memory['quiet_users']:
        to_prune = list()
        for user in bot.memory['quiet_users'][channel]:
            if bot.memory['quiet_users'][channel][user] + timedelta(minutes=30) < datetime.now():
                to_prune.append(user)
        for user in to_prune:
            bot.write(['mode', channel, '-q', user])
            del bot.memory['quiet_users'][channel][user]

def make_user_quiet(bot,channel, nick):
    if channel not in bot.memory['quiet_users']:
        bot.memory['quiet_users'][channel] = dict()
    bot.memory['quiet_users'][channel][nick] = datetime.now()

@require_privilege(VOICE)
@sopel.module.rule(r'.*')
@sopel.module.priority('low')
def make_user_active(bot, trigger):
    channel = trigger.sender
    nick = trigger.account
    if nick is None:
        return
    if channel not in bot.memory['active_users']:
        bot.memory['active_users'][channel] = dict()
    bot.memory['active_users'][channel][nick] = datetime.now()
    clear_protection(bot, channel)
    clear_quiets(bot)
    prune_active_users(bot)

@sopel.module.commands('activeusers')
@sopel.module.example('.activeusers')
def show_active_users(bot, trigger):
    make_user_active(bot, trigger)
    channel = trigger.sender
    if channel not in bot.memory['active_users']:
        bot.say("No active users")
        return
    bot.say("There are %s eligible voters active in %s" % (str(len(bot.memory['active_users'][channel])), channel))

def calculate_quota(bot, trigger, mode):
    channel = trigger.sender
    quota = int(max(floor(len(bot.memory['active_users'][channel])*mode), 1))
    return quota

def do_kick(bot, channel, target):
    bot.write(['KICK', channel, target], "You have been voted off the island.")

def do_ban(bot, channel, target):
    bot.msg('chanserv', 'AKICK %s ADD %s!*@* !T 120 Users have voted you out of the channel for 2 hours.' % (channel, target))

def do_quiet(bot, channel, target):
    make_user_quiet(bot, channel, target)
    bot.write(['mode', channel, '+q', target])

def do_voice(bot, channel, target):
    bot.write(['mode', channel, '-q', target])
    bot.write(['mode', channel, '+v', target])

def do_registered(bot, channel):
    bot.write(['mode', channel, '+r'])
    bot.memory['protected_timestamp'] = datetime.now()

def do_moderated(bot, channel):
    bot.write(['mode', channel, '+m'])
    bot.memory['protected_timestamp'] = datetime.now()

def votemode(bot, trigger, mode):
    make_user_active(bot, trigger)
    channel = trigger.sender
    nick = trigger.account
    if nick is None:
        bot.say("You must be authed to use this command")
        return
    if bot.privileges[trigger.sender][bot.nick] < OP:
        return bot.reply("I'm not a channel operator!")
    quota = calculate_quota(bot, trigger, bot.memory['mode_threshold'][mode])
    # This isn't per user but it's probably an OK heuristic
    if datetime.now() - bot.memory['last_vote'] > timedelta(minutes=5):
        clear_votes(bot)
    # Quota is 50% of active users plus one
    if trigger.group(2):
        target = Identifier(str(trigger.group(2)).split()[0].strip().lower())
        if not target.is_nick():
            return bot.reply("That is not a valid nick")
        if target not in bot.privileges[channel]:
            return bot.reply("I don't see %s." % target)
        target_privs = bot.privileges[channel][target]
        if target_privs > 0:
            return bot.reply("You cannot vote" + mode + " privileged users")

        if target in bot.memory['votes'][mode]:
            if str(nick) not in bot.memory['votes'][mode][target]:
                bot.memory['votes'][mode][target].append(str(nick))
        else:
            bot.memory['votes'][mode][target] = [str(nick)]

        bot.reply("Vote recorded. (%s more votes for action)" % str(max(0, quota - len(bot.memory['votes'][mode][target])+1)))

        if len(bot.memory['votes'][mode][target]) > quota:
            bot.memory['vote_methods'][mode](bot, channel, target)
        bot.memory['last_vote'] = datetime.now()
    elif mode == "registered" or mode == "moderated":
        if str(nick) not in bot.memory['votes'][mode]:
            bot.memory['votes'][mode].append(str(nick))
        else:
            bot.memory['votes'][mode] = [str(nick)]
        bot.reply("Vote recorded. (%s more votes for action)" % str(max(0, quota - len(bot.memory['votes'][mode])+1)))
        if len(bot.memory['votes'][mode]) > quota:
            bot.memory['vote_methods'][mode](bot, channel)
        bot.memory['last_vote'] = datetime.now()
    else:
        bot.say("Current active vote%s (%s needed to %s): " % (mode, str(quota + 1), mode))
        for ballot in bot.memory['votes'][mode]:
            bot.say("%s has %s %s votes." % (ballot, len(bot.memory['votes'][mode][ballot]), mode))
        return

@require_privilege(VOICE)
@sopel.module.commands('voteban', 'voteb')
def voteban(bot, trigger):
    votemode(bot, trigger, 'ban')

@require_privilege(VOICE)
@sopel.module.commands('votekick', 'votek')
def votekick(bot, trigger):
    votemode(bot, trigger, 'kick')

@require_privilege(VOICE)
@sopel.module.commands('votevoice', 'votev')
def votevoice(bot, trigger):
    votemode(bot, trigger, 'voice')

@require_privilege(VOICE)
@sopel.module.commands('votequiet', 'voteq')
def votequiet(bot, trigger):
    votemode(bot, trigger, 'quiet')

@require_privilege(VOICE)
@sopel.module.commands('voteregistered', 'voter')
def voteregistered(bot, trigger):
    votemode(bot, trigger, 'registered')

@require_privilege(VOICE)
@sopel.module.commands('votemoderated', 'votem')
def votemoderated(bot, trigger):
    votemode(bot, trigger, 'moderated')

@require_privilege(VOICE)
@sopel.module.commands('bunnies')
def nuclear_option(bot, trigger):
    channel = trigger.sender
    nick = trigger.nick
    bot.say("Bunnies are wonderful creatures. I enjoy watching them frolic.")
    bot.action('watches the bunnies frolic.')
    if bot.privileges[channel][bot.nick] < OP:
        return
    elif bot.privileges[channel][nick] < OP:
        return
    safety = str(trigger.group(2)).strip()
    if nick != "aletheist" or str(safety) != "!":
        return
    sleep(5)
    bot.say("Nuclear launch detected.")
    sleep(10)
    bot.msg('chanserv', 'CLEAR %s USERS Nuclear option executed.' % channel)

