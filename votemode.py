import sopel
from sopel.module import commands, priority, OP, HALFOP, VOICE, require_privilege
from sopel.tools import Identifier
from enum import Enum
from math import ceil
from datetime import datetime
from datetime import timedelta

def setup(bot):
  bot.memory['active_users'] = dict()
  bot.memory['last_votekick'] = datetime.now()
  bot.memory['ban_votes'] = dict()
  bot.memory['last_voteban'] = datetime.now()
  bot.memory['kick_votes'] = dict()

class Modes(Enum):
    Kick = .5
    Ban = .66
    Voice = .25
    Moderated = .3
    RegisteredOnly = .4

def prune_active_users(bot):
  for c in bot.memory['active_users']:
    to_prune = list()
    for u in bot.memory['active_users'][c]:
      print('DEBUG: Removing %s' % bot.memory['active_users'][c][u])
      if bot.memory['active_users'][c][u] + timedelta(minutes=5) < datetime.now():
        to_prune.append(u)
    for u in to_prune:
      del bot.memory['active_users'][c][u]

@require_privilege(VOICE)
@sopel.module.rule(r'.*')
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
    bot.reply("No active users")
    return
  prune_active_users(bot)
  bot.reply("Users active in %s: " % channel)
  for u in bot.memory['active_users'][channel]:
    bot.reply("%s" % u)

def calculate_quota(bot, trigger, threshold):
  channel = trigger.sender
  quota = (ceil(len(bot.memory['active_users'][channel])*threshold))
  return quota

#def votemode(bot, mode):

@require_privilege(VOICE)
@sopel.module.commands('votekick')
def votekick(bot, trigger):
  make_user_active(bot, trigger)
  channel = trigger.sender
  nick = trigger.nick
  quota = calculate_quota(bot, trigger, 0.5) 
  prune_active_users(bot)
  # This isn't per user but it's probably an OK heuristic
  if datetime.now() - bot.memory['last_votekick'] > timedelta(minutes=5):
    bot.memory['kick_votes'] = dict()
  # Quota is 50% of active users plus one
  if trigger.group(2):
    target = str(trigger.group(2)).strip()
    if not Identifier(target).is_nick():
      bot.reply("That is not a valid nick")
      return
    if target not in bot.privileges[channel]:
      bot.reply("I don't see that user.")
      return
    target_privs = bot.privileges[channel][target]
    if target_privs > 0:
     bot.reply("You cannot votekick privileged users")
     return
    
    if target in bot.memory['kick_votes']:
      if str(nick) not in bot.memory['kick_votes'][target]:
        bot.memory['kick_votes'][target].append(str(nick))
    else:
      bot.memory['kick_votes'][target] = list()
      bot.memory['kick_votes'][target].append(str(nick))
    bot.reply("Vote recorded.")
    
    if len(bot.memory['kick_votes'][target]) > quota:
      bot.write(['KICK', channel, target], "You have been voted off the island.")
    bot.memory['last_votekick'] = datetime.now()
  else:
    bot.say("Current active votekicks (%s needed to kick): " % str(quota + 1))
    for ballot in bot.memory['kick_votes']:
      bot.say("%s has %s kick votes." % (ballot, len(bot.memory['kick_votes'][ballot])))
    return

