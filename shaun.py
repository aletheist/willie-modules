import random

import sopel

@sopel.module.rule(r'.+')
def shaun(bot, trigger):
    if random.randint(1,50000) == 50000:
        say_shaun(bot)

@sopel.module.commands('shaun')
def shaun_explicit(bot, trigger):
    say_shaun(bot)

def say_shaun(bot):
    bot.say('SHA' + ('U' * random.randint(1,10)) + 'N')
