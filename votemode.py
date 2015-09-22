import sopel
from datetime import datetime
from datetime import timedelta

active_users=dict()

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

@sopel.module.rule(r'.*')
def make_user_active(bot, trigger):
  global active_users
  channel = trigger.sender
  nick = trigger.nick
  if channel not in active_users:
    active_users[channel] = dict()
  active_users[channel][nick] = datetime.now()

@sopel.module.commands('activeusers')
@sopel.module.example('.active users')
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

