import operator

import willie

def setup(bot):
    if not bot.memory.contains('heretics2'):
        bot.memory['heretics2'] = willie.tools.WillieMemory()

@willie.module.rule(r'(\w+) is a heretic')
def denounce_heretic(bot, trigger):
    target = trigger.group(1)
    if target in bot.memory['heretics2']:
        # Target has been denounced or denied before. Check for this user's judgment
        if trigger.nick in bot.memory['heretics2'][target]['no']:
            # User has changed his mind; remove from list of "no"s
            bot.memory['heretics2'][target]['no'].remove(trigger.nick)

        if trigger.nick not in bot.memory['heretics2'][target]['yes']:
            # User has not denounced target before; add to list of "yes"s
            bot.memory['heretics2'][target]['yes'].append(trigger.nick)
    else:
        # Target has not been seen before - initialize memory
        bot.memory['heretics2'][target] = {
            'yes': [ trigger.nick ],
            'no' : []
        }
    bot.say('noted')

@willie.module.rule(r'(\w+) is not a heretic')
def deny_heresy(bot, trigger):
    target = trigger.group(1)
    if target in bot.memory['heretics2']:
        # Target has been denounced or denied before. Check for this user's judgment
        if trigger.nick in bot.memory['heretics2'][target]['yes']:
            # User has changed his mind; remove from list of "yes"s
            bot.memory['heretics2'][target]['yes'].remove(trigger.nick)

        if trigger.nick not in bot.memory['heretics2'][target]['no']:
            # User has not denied target before; add to list of "no"s
            bot.memory['heretics2'][target]['no'].append(trigger.nick)
    else:
        # Target has not been seen before - initialize memory
        bot.memory['heretics2'][target] = {
            'yes': [],
            'no' : [ trigger.nick ]
        }
    bot.say('noted')

def total_denunciations(target):
    return (target[0], len(target[1]['yes']) - len(target[1]['no']))

@willie.module.commands('heretics')
@willie.module.example('.heretics')
def heretics(bot, trigger):            
    bot.say('Top Heretics')
    for i, heretic in enumerate([ x for x in sorted(map(total_denunciations, bot.memory['heretics2'].iteritems()), key=operator.itemgetter(1), reverse=True) if x[1] > 0][:5]):
        bot.say('  #' + str(i + 1) + ' ' + heretic[0] + ' (' + str(heretic[1]) + ' denunciation' + ('s' if heretic[1] != 1 else '') + ')')

@willie.module.commands('heretic')
@willie.module.example('.heretic')
def heretic(bot, trigger):
    target = trigger.nick
    if trigger.group(2):
        target = trigger.group(2)

    if target in bot.memory['heretics2']:
        obj = bot.memory['heretics2'][target]
        total = len(obj['yes']) - len(obj['no'])
        bot.say(target + ' (' + str(total) + ' denunciation' + ('s' if total != 1 else '') + ')')
    else:
        bot.say(target + ' (0 denunciations)')
