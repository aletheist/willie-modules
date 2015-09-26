import sopel
from datetime import datetime
from datetime import timedelta

active_users = dict()
last_votekit = datetime.now()
ban_votes = dict()
last_voteban = datetime.now()
kick_votes = dict()

def prune_active_users():
  global active_users
  for c in active_users:
    to_prune = list()
    for u in active_users[c]:
      print('DEBUG: Removing %s' % active_users[c][u])
      if active_users[c][u] + timedelta(seconds=5) < datetime.now():
        to_prune.append(u)
    for u in to_prune:
      del active_users[c][u]

@require_privilege(VOICE)
@sopel.module.rule(r'.*')
def make_user_active(bot, trigger):
  global active_users
  channel = trigger.sender
  nick = trigger.nick
  if channel not in active_users:
    active_users[channel] = dict()
  active_users[channel][nick] = datetime.now()

@sopel.module.commands('activeusers')
@sopel.module.example('.activeusers')
def show_active_users(bot, trigger):
  global active_users
  channel = trigger.sender
  nick = trigger.nick
  if channel not in active_users:
    bot.reply("No active users")
    return
  prune_active_users()
  bot.reply("Users active in %s: " % channel)
  for u in active_users[channel]:
    bot.reply("%s" % u)

@require_privilege(VOICE)
@sopel.module.commands('votekick')
def votekick(bot, trigger):
  global last_votekick
  channel = trigger.sender
  nick = trigger.nick
  quota = (len(active_users[channel])/2)
  # This isn't per user but it's probably an OK heuristic
  if datetime.now() - last_votekick > timedelta(minutes=5):
    kick_votes = dict()
  # Quota is 50% of active users plus one
  if trigger.group(2):
    target = trigger.group(2)
    target_privs = bot.privileges[trigger.sender]
    if target_privs > 0:
     bot.reply("You cannot votekick privileged users")
     return
    if target in kick_votes:
      kick_votes[target] = kick_votes[target] + 1
    else:
      kick_votes[target] = 1
    if kick_votes[target] > quota:
      bot.write(['KICK', channel, target], "You have been voted off the island.")
  else:
    for ballot in kick_votes:
      bot.reply("%s has %s kick votes." % (target, kick_votes[target])
    return
