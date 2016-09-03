import random
import datetime
import sopel

def setup(bot):
    bot.cap_req('denom', 'extended-join')
    bot.cap_req('denom', 'account-notify')
    if not bot.memory.contains('denom_nick_last_query'):
        bot.memory['denom_nick_last_query'] = sopel.tools.SopelMemory()
    if not bot.memory.contains('denom_nick_fast_query_count'):
        bot.memory['denom_nick_fast_query_count'] = sopel.tools.SopelMemory()
    if not bot.memory.contains('denom_nick_reply_via_message'):
        bot.memory['denom_nick_reply_via_message'] = sopel.tools.SopelMemory()

def claim_nick(bot, account, alias):
  if account is None:
    return
  if account.lower() == alias.lower():
    return
  try:
    # First we try to unalias the person
    bot.db.unalias_nick(alias)
    if account != alias:
      try:
        # If we were able to unalias, now stick that nick on the new account
        # Someone can steal a nick within the ghosting time limit unfortunately
        bot.db.alias_nick(account, alias)
      except ValueError as e:
        pass
  except ValueError as e:
    # If it's not an alias, we merge instead
    bot.db.merge_nick_groups(account, alias) 

@sopel.module.commands('setdenom', 'mydenom')
@sopel.module.example('.setdenom Lutheran')
def set_denom(bot, trigger):
  '''Set a user's denomination'''
  length_limit = 128
  person = str(trigger.nick)
  account = trigger.account
  sender = trigger.sender
  denom = 'Trout'
  if trigger.group(2):
    denom = trigger.group(2)

  if account is None:
    bot.msg(sender, 'Sorry, you need to be authed to services to use this command.')
  elif len(denom) > length_limit:
    bot.reply('Denomination name too long. (Limit %s characters)' % str(length_limit))
  else:
    claim_nick(bot, account, person)
    bot.db.set_nick_value(account, 'denom', denom)
    bot.msg(sender, 'Got it: %s is %s' % (person, denom))

@sopel.module.commands('denom', 'getdenom')
@sopel.module.example('.denom mstark')
def get_denom(bot, trigger):
  if trigger.group(2):
    person = trigger.group(2)
  else:
    person = str(trigger.nick)
    claim_nick(bot, trigger.account, person)

  reply_via_msg = False

  if trigger.nick != trigger.sender:
    now = datetime.datetime.now()
    if person in bot.memory['denom_nick_last_query']:
        elapsed_since_last = (now - bot.memory['denom_nick_last_query'][person]).total_seconds()
        if elapsed_since_last < 10:
            if person in bot.memory['denom_nick_fast_query_count']:
                bot.memory['denom_nick_fast_query_count'][person] += 1
            else:
                bot.memory['denom_nick_fast_query_count'][person] = 1
        else:
            # reset
            if person in bot.memory['denom_nick_fast_query_count']:
                bot.memory['denom_nick_fast_query_count'][person] = 0
            if person in bot.memory['denom_nick_reply_via_message'] and bot.memory['denom_nick_reply_via_message'][person] is True:
                bot.memory['denom_nick_reply_via_message'][person] = False
    bot.memory['denom_nick_last_query'][person] = now

    if person in bot.memory['denom_nick_fast_query_count']:
        if bot.memory['denom_nick_fast_query_count'][person] > 2:
            if person not in bot.memory['denom_nick_reply_via_message'] or bot.memory['denom_nick_reply_via_message'][person] is False:
                bot.memory['denom_nick_reply_via_message'][person] = True
                bot.reply('Sending further replies as private messages.')
            reply_via_msg = True

  if reply_via_msg:
    if bot.db.get_nick_value(person,'denom'):
      bot.msg(person, '%s is %s' % (person, bot.db.get_nick_value(person,'denom')))
    else:
      bot.msg(person, 'I don\'t know what %s is.' % person)
  else:
    if bot.db.get_nick_value(person,'denom'):
      bot.reply('%s is %s' % (person, bot.db.get_nick_value(person,'denom')))
    else:
      bot.reply('I don\'t know what %s is.' % person)

