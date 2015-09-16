import sopel

@sopel.module.commands('setdenom', 'mydenom')
@sopel.module.example('.setdenom Lutheran')
def set_denom(bot, trigger):
  '''Check whether something (or someone) is honorable'''
  person = str(trigger.nick)
  denom = 'Goof'
  if trigger.group(2):
    denom = trigger.group(2)

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