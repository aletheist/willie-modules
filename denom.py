import sopel

@sopel.module.commands('setdenom', 'mydenom')
@sopel.module.example('.setdenom Lutheran')
def set_denom(bot, trigger):
  '''Set a user's denomination'''
  length_limit = 128
  person = str(trigger.nick)
  denom = 'Trout'
  if trigger.group(2):
    denom = trigger.group(2)

  if len(denom) > length_limit:
    bot.reply('Denomination name too long. (Limit %s characters)' % str(length_limit))
    return

  bot.db.set_nick_value(person, 'denom', denom)
  bot.reply('Got it: %s is %s' % (person, denom))

@sopel.module.commands('denom', 'getdenom')
@sopel.module.example('.denom mstark')
def get_denom(bot, trigger):
  person = trigger.nick
  if trigger.group(2):
    person = trigger.group(2)

  if bot.db.get_nick_value(person,'denom'):
    bot.reply('%s is %s' % (person, bot.db.get_nick_value(person,'denom')))
  else:
    bot.reply('I don\'t know what %s is.' % person)
