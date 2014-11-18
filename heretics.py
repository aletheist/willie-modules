import operator

import willie

def setup(bot):
    if not bot.memory.contains('heretics'):
        bot.memory['heretics'] = willie.tools.WillieMemory()

@willie.module.rule(r'\b([a-zA-Z][a-zA-Z0-9\[\]\-\\`^{}\_]*) is a(?:n)? heretic\b')
@willie.module.rule(r'\b([a-zA-Z][a-zA-Z0-9\[\]\-\\`^{}\_]*) are heretics\b')
def denounce_heretic(bot, trigger):
    target = trigger.group(1)
    if target not in bot.memory['heretics']:
        init_heretic_target(bot, target)
    # Check for this user's judgment
    if trigger.nick in bot.memory['heretics'][target]['no']:
        # User has changed his mind; remove from list of "no"s
        bot.memory['heretics'][target]['no'].remove(trigger.nick)

    if trigger.nick not in bot.memory['heretics'][target]['yes']:
        # User has not denounced target before; add to list of "yes"s
        bot.memory['heretics'][target]['yes'].append(trigger.nick)
    bot.say('noted')

@willie.module.rule(r'\b([a-zA-Z][a-zA-Z0-9\[\]\-\\`^{}\_]*) is not a(?:n)? heretic\b')
@willie.module.rule(r'\b([a-zA-Z][a-zA-Z0-9\[\]\-\\`^{}\_]*) are not heretics\b')
def deny_heresy(bot, trigger):
    target = trigger.group(1)
    if target not in bot.memory['heretics']:
        init_heretic_target(bot, target)
    # Check for this user's judgment
    if trigger.nick in bot.memory['heretics'][target]['yes']:
        # User has changed his mind; remove from list of "yes"s
        bot.memory['heretics'][target]['yes'].remove(trigger.nick)

    if trigger.nick not in bot.memory['heretics'][target]['no']:
        # User has not denied target before; add to list of "no"s
        bot.memory['heretics'][target]['no'].append(trigger.nick)
    bot.say('noted')

def init_heretic_target(bot, target):
    bot.memory['heretics'][target] = { 'yes': [], 'no': [] }

def total_denunciations(target):
    return (target[0], len(target[1]['yes']) - len(target[1]['no']))

@willie.module.commands('heretics')
@willie.module.example('.heretics')
def heretics(bot, trigger):
    '''Lists the top 5 known heretics.'''
    num = 5
    try:
        num = min(int(trigger.group(2)), 10) # Max out at 10 heretics to avoid spam (*ahem* ALETHEIST *ahem*)
    except:
        pass
    bot.say('Top %d Heretics' % num)
    for i, heretic in enumerate([ x for x in sorted(map(total_denunciations, bot.memory['heretics'].iteritems()), key=operator.itemgetter(1), reverse=True) if x[1] > 0][:num]):
        bot.say('  #' + str(i + 1) + ' ' + heretic[0] + ' (' + str(heretic[1]) + ' denunciation' + ('s' if heretic[1] != 1 else '') + ')')

@willie.module.commands('heretic')
@willie.module.example('.heretic Spong')
def heretic(bot, trigger):
    '''Shows the "heretic score" of the given target, or the user if no target is given.'''
    target = trigger.nick
    if trigger.group(2):
        target = trigger.group(2)

    if target in bot.memory['heretics']:
        obj = bot.memory['heretics'][target]
        total = len(obj['yes']) - len(obj['no'])
        bot.say(target + ' (' + str(total) + ' denunciation' + ('s' if total != 1 else '') + ')')
    else:
        bot.say(target + ' (0 denunciations)')
