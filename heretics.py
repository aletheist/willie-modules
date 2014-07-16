import operator

import willie

def setup(bot):
    if not bot.memory.contains('heretics'):
        bot.memory['heretics'] = willie.tools.WillieMemory()

@willie.module.rule(r'(\w+) is a heretic')
def denounce_heretic(bot, trigger):
    if trigger.group(1) in bot.memory['heretics']:
        bot.memory['heretics'][trigger.group(1)] += 1
    else:
        bot.memory['heretics'][trigger.group(1)] = 1
    bot.say('noted')

@willie.module.rule(r'(\w+) is not a heretic')
def deny_heresy(bot, trigger):
    if trigger.group(1) in bot.memory['heretics']:
        bot.memory['heretics'][trigger.group(1)] -= 1
    else:
        bot.memory['heretics'][trigger.group(1)] = -1
    bot.say('noted')

@willie.module.commands('heretics')
@willie.module.example('.heretics')
def heretics(bot, trigger):
    bot.say('Top Heretics')
    for i, heretic in enumerate([ x for x in sorted(bot.memory['heretics'].iteritems(), key=operator.itemgetter(1), reverse=True) if x[1] > 0 ][:5]):
        bot.say('  #' + str(i + 1) + ' ' + heretic[0] + ' (' + str(heretic[1]) + ' denunciation' + ('s' if heretic[1] != 1 else '') + ')')

@willie.module.commands('heretic')
@willie.module.example('.heretic')
def heretic(bot, trigger):
    if trigger.nick in bot.memory['heretics']:
        if bot.memory['heretics'][trigger.nick] > 0:
            bot.say(trigger.nick + ' is a heretic')
        else:
            bot.say(trigger.nick + ' is not a heretic')
    else:
        bot.say(trigger.nick + ' is not a heretic')
