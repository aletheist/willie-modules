import sopel
from sopel.module import commands, priority, OP, HALFOP, VOICE, require_privilege
from sopel.tools import Identifier
from math import floor
from datetime import datetime
from datetime import timedelta
from time import sleep

def clear_votes(bot):
    bot.memory['ban_votes'] = dict()
    bot.memory['kick_votes'] = dict()
    bot.memory['voice_votes'] = dict()
    bot.memory['registered_votes'] = dict()
    bot.memory['moderated_votes'] = dict()

def setup(bot):
    bot.memory['active_users'] = dict()
    bot.memory['last_vote'] = datetime.now()
    bot.memory['mode_threshold'] = dict()
    bot.memory['mode_threshold']['kick'] = 0.5
    bot.memory['mode_threshold']['ban'] = 0.66
    bot.memory['mode_threshold']['moderated'] = 0.3
    bot.memory['mode_threshold']['registered'] = 0.4
    bot.memory['mode_threshold']['voice'] = 0.4
    clear_votes(bot)

def prune_active_users(bot):
    for channel in bot.memory['active_users']:
        to_prune = list()
        for user in bot.memory['active_users'][channel]:
            if bot.memory['active_users'][channel][user] + timedelta(minutes=15) < datetime.now():
                to_prune.append(user)
        for user in to_prune:
            del bot.memory['active_users'][channel][user]

@require_privilege(VOICE)
@sopel.module.rule(r'.*')
@sopel.module.priority('low')
def make_user_active(bot, trigger):
    channel = trigger.sender
    nick = trigger.nick
    if channel not in bot.memory['active_users']:
        bot.memory['active_users'][channel] = dict()
    bot.memory['active_users'][channel][nick] = datetime.now()

@sopel.module.commands('activeusers')
@sopel.module.example('.activeusers')
def show_active_users(bot, trigger):
    channel = trigger.sender
    nick = trigger.nick
    if channel not in bot.memory['active_users']:
        bot.say("No active users")
        return
    prune_active_users(bot)
    bot.say("There are %s eligible voters active in %s" % (str(len(bot.memory['active_users'][channel])), channel))

def calculate_quota(bot, trigger, mode):
    channel = trigger.sender
    quota = max(floor(len(bot.memory['active_users'][channel])*mode), 1)
    return quota

def votemode(bot, trigger, mode):
    make_user_active(bot, trigger)
    channel = trigger.sender
    nick = trigger.nick
    if bot.privileges[trigger.sender][bot.nick] < OP:
        return bot.reply("I'm not a channel operator!")
    quota = calculate_quota(bot, trigger, bot.memory['mode_threshold'][mode]) 
    prune_active_users(bot)
    # This isn't per user but it's probably an OK heuristic
    if datetime.now() - bot.memory['last_vote'] > timedelta(minutes=5):
        clear_votes(bot)
    # Quota is 50% of active users plus one
    if trigger.group(2):
        target = str(trigger.group(2)).strip().lower()
        if not Identifier(target).is_nick():
            return bot.reply("That is not a valid nick")
        if target not in bot.privileges[channel]:
            return bot.reply("I don't see that user.")
        target_privs = bot.privileges[channel][target]
        if target_privs > 0:
            return bot.reply("You cannot vote" + mode + " privileged users")
        
        if target in bot.memory[mode+'_votes']:
            if str(nick) not in bot.memory[mode+'_votes'][target]:
                bot.memory[mode+'_votes'][target].append(str(nick))
        else:
            bot.memory[mode+'_votes'][target] = list()
            bot.memory[mode+'_votes'][target].append(str(nick))
        bot.reply("Vote recorded.")
        
        if len(bot.memory[mode+'_votes'][target]) > quota:
            if mode == 'kick':
                bot.write(['KICK', channel, target], "You have been voted off the island.")
            elif mode == 'ban':
                bot.msg('chanserv', 'AKICK %s ADD %s!*@* !T 30 Users have voted you out of the channel for 30 minutes.' % (channel, target))
            elif mode == 'voice':
                bot.write(['mode', channel, '+v', target])
                bot.say("%s has been granted voice." % target)
            elif mode == 'registered':
                bot.write(['KICK', channel, target], "You have been banned for 30 minutes.")
                bot.say("Channel set to allow only registered users to join for 30 minutes.")
            elif mode == 'moderated':
                bot.write(['KICK', channel, target], "You have been banned for 30 minutes.")
                bot.say("Channel set to moderated for 30 minutes.")

        bot.memory['last_vote'] = datetime.now()
    else:
        bot.say("Current active vote%s (%s needed to %s): " % (mode, str(quota + 1), mode))
        for ballot in bot.memory[mode+'_votes']:
            bot.say("%s has %s %s votes." % (ballot, len(bot.memory[mode+'_votes'][ballot]), mode))
        return

@require_privilege(VOICE)
@sopel.module.commands('voteban')
def voteban(bot, trigger):
    votemode(bot, trigger, 'ban')

@require_privilege(VOICE)
@sopel.module.commands('votekick')
def votekick(bot, trigger):
    votemode(bot, trigger, 'kick')

@require_privilege(VOICE)
@sopel.module.commands('votevoice')
def votevoice(bot, trigger):
    votemode(bot, trigger, 'voice')

@require_privilege(OP)
@sopel.module.commands('bunnies')
def nuclear_option(bot, trigger):
    channel = trigger.sender
    nick = trigger.nick
    bot.say("Bunnies are wonderful creatures. I enjoy watching them frolic.")
    bot.action('watches the bunnies frolic.')
    if nick != "aletheist":
        return
    sleep(5)
    bot.say("Nuclear launch detected.")
    sleep(10)
    bot.msg('chanserv', 'CLEAR %s USERS Nuclear option executed.' % channel)

