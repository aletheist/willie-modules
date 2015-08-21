import sopel

@sopel.module.rule(r'.*midget.*')
def midget(bot, trigger):
    bot.say('*non-PC language detected*')
