import sopel

@sopel.module.rule(r'.*(?:[Cc]hrist|[Hh]e|[Tt]he [Ll]ord) is risen[\.!]?$')
def risen(bot, trigger):
    bot.say('He is risen indeed!')
