import sopel
from sopel.module import commands, priority, OP, HALFOP, VOICE, require_privilege
from datetime import datetime
from datetime import timedelta

def setup(bot):
  bot.memory['active_users'] = dict()
  bot.memory['last_votekick'] = datetime.now()
  bot.memory['ban_votes'] = dict()
  bot.memory['last_voteban'] = datetime.now()
  bot.memory['kick_votes'] = dict()

def prune_active_users(bot):
  for c in bot.memory['active_users']:
    to_prune = list()
    for u in bot.memory['active_users'][c]:
      print('DEBUG: Removing %s' % bot.memory['active_users'][c][u])
      if bot.memory['active_users'][c][u] + timedelta(seconds=5) < datetime.now():
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

@require_privilege(VOICE)
@sopel.module.commands('votekick')
def votekick(bot, trigger):
  channel = trigger.sender
  nick = trigger.nick
  quota = (len(bot.memory['active_users'][channel])/2)
  # This isn't per user but it's probably an OK heuristic
  if datetime.now() - bot.memory['last_votekick'] > timedelta(minutes=5):
    bot.memory['kick_votes'] = dict()
  # Quota is 50% of active users plus one
  if trigger.group(2):
    target = trigger.group(2)
    target_privs = bot.privileges[channel][target]
    if target_privs > 0:
     bot.reply("You cannot votekick privileged users")
     return
    
    if target in bot.memoery['kick_votes']:
      bot.memory['kick_votes'][target] = bot.memory['kick_votes'][target] + 1
    else:
      bot.memory['kick_votes'][target] = 1
    
    if bot.memory['kick_votes'][target] > quota:
      bot.write(['KICK', channel, target], "You have been voted off the island.")
    bot.memory['last_votekick'] = datetime.now()
  else:
    bot.reply("Current active votes: ")
    for ballot in bot.memory['kick_votes']:
      bot.reply("%s has %s kick votes." % (ballot, bot.memory['kick_votes'][ballot]))
    return

