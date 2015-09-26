import random
import datetime
import sopel

def setup(bot):
    if not bot.memory.contains('denom_nick_last_query'):
        bot.memory['denom_nick_last_query'] = sopel.tools.SopelMemory()
    if not bot.memory.contains('denom_nick_fast_query_count'):
        bot.memory['denom_nick_fast_query_count'] = sopel.tools.SopelMemory()
    if not bot.memory.contains('denom_nick_reply_via_message'):
        bot.memory['denom_nick_reply_via_message'] = sopel.tools.SopelMemory()
    if not bot.memory.contains('denom_ns_pending_checks'):
        bot.memory['denom_ns_pending_checks'] = sopel.tools.SopelMemory()
    if not bot.memory.contains('denom_ns_checking'):
        bot.memory['denom_ns_checking'] = None

@sopel.module.commands('setdenom', 'mydenom')
@sopel.module.example('.setdenom Lutheran')
def set_denom(bot, trigger):
  '''Set a user's denomination'''
  length_limit = 128
  person = str(trigger.nick).lower()
  sender = trigger.sender
  denom = 'Trout'
  if trigger.group(2):
    denom = trigger.group(2)

  if len(denom) > length_limit:
    bot.reply('Denomination name too long. (Limit %s characters)' % str(length_limit))
    return

  bot.memory['denom_ns_pending_checks'][person] = [ sender, denom ]
  bot.msg('NickServ', 'INFO ' + person + ' ' + str(random.randint(0,100))) # random character means that WorfBot will never send '...' after repeating himself, which otherwise is possible because hardcoded into sopel's irc.py

@sopel.module.commands('denom', 'getdenom')
@sopel.module.example('.denom mstark')
def get_denom(bot, trigger):
  person = str(trigger.nick)
  if trigger.group(2):
    person = trigger.group(2)

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
      bot.msg(person, '%s is %s' % (person, bot.db.get_nick_value(person.lower(),'denom')))
    else:
      bot.msg(person, 'I don\'t know what %s is.' % person)
  else:
    if bot.db.get_nick_value(person,'denom'):
      bot.reply('%s is %s' % (person, bot.db.get_nick_value(person.lower(),'denom')))
    else:
      bot.reply('I don\'t know what %s is.' % person)

@sopel.module.event('NOTICE')
@sopel.module.rule('Information on \x02(.*)\x02 \(account \x02(.*)\x02\):')
def nickserv_info_account(bot, trigger):
    person = trigger.nick
    groups = [ x.lower() for x in trigger.groups() ]
    if person == 'NickServ' and groups[0] == groups[1]:
        if groups[0] in bot.memory['denom_ns_pending_checks']:
            # this person is authenticated to NickServ and on their account, so they proceed to the next level
            bot.memory['denom_ns_checking'] = groups[0]
    else:
        # they failed the requirements
        if groups[0] in bot.memory['denom_ns_pending_checks']:
            sender = bot.memory['denom_ns_pending_checks'][groups[0]][0]
            del bot.memory['denom_ns_pending_checks'][groups[0]]
            bot.msg(sender, 'Sorry, you need to be authed to services to use this command.')

@sopel.module.event('NOTICE')
@sopel.module.rule('Last seen  : (.+)')
def nickserv_info_last_seen(bot, trigger):
    person = trigger.nick
    groups = trigger.groups()
    if person == 'NickServ' and groups[0] == 'now':
        if bot.memory['denom_ns_checking'] in bot.memory['denom_ns_pending_checks']:
            # whoever we're currently checking is currently authed
            nickname = bot.memory['denom_ns_checking']
            sender, denom = bot.memory['denom_ns_pending_checks'][nickname]
            bot.db.set_nick_value(nickname, 'denom', denom)
            del bot.memory['denom_ns_pending_checks'][nickname]
            bot.memory['denom_ns_checking'] = None
            bot.msg(sender, 'Got it: %s is %s' % (nickname, denom))
        else:
            # this should never happen
            bot.memory['denom_ns_checking'] = None
    else:
        # they failed the requirements
        if bot.memory['denom_ns_checking'] is not None:
            sender = bot.memory['denom_ns_pending_checks'][bot.memory['denom_ns_checking']][0]
            del bot.memory['denom_ns_pending_checks'][bot.memory['denom_ns_checking']]
            bot.memory['denom_ns_checking'] = None
            bot.msg(sender, 'Sorry, you need to be authed to services to use this command.')
