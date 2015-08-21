import sopel

@sopel.module.rule(r'^\.suicidehotline (#?\S+) ?(.+)?')
def shaun(bot, trigger):
    if trigger.group(2) is None:
        bot.msg(trigger.group(1), 'Need help? There is hope! In the U.S., call 1-800-273-8255. Many other countries provide hotlines as well, http://www.suicide.org/international-suicide-hotlines.html')
    else:
        bot.msg(trigger.group(1), trigger.group(2))
