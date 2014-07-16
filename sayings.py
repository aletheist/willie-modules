import random

import willie

def setup(bot):
    if not bot.memory.contains('sayings'):
        bot.memory['sayings'] = willie.tools.WillieMemory()
    if not bot.memory.contains('sayings_votes_forget'):
        bot.memory['sayings_votes_forget'] = willie.tools.WillieMemory()

def talk_about(bot, subject):
    line = random.choice([ 'i heard that', 'it has been said that', 'someone said', 'it was said that', 'it was once said that', '' ])
    if bot.memory['sayings'][subject][0] == 'is':
        verb = random.choice([ 'is', 'was' ])
    else:
        verb = random.choice([ 'are', 'were' ])
    punctuation = random.choice([ '.', '...', '!' ])
    bot.say(line + (' ' if len(line) > 0 else '') + subject + ' ' + verb + ' ' + bot.memory['sayings'][subject][1] + punctuation)

#@willie.module.rule(r'(\w+)\?')
@willie.module.rule(r'([\w ]+)')
def sayings(bot, trigger):
    if trigger.group(1) in bot.memory['sayings']:
        if random.randint(1,10) == 10:
            talk_about(bot, trigger.group(1))

#@willie.module.rule(r'(\w+) (?:is|=) ([\w ]+)')
@willie.module.rule(r'([\w ]+) (?:is|=) ([\w ]+)')
def record_is(bot, trigger):
    if trigger.group(1) not in bot.memory['sayings']:
        bot.memory['sayings'][trigger.group(1)] = [ 'is', trigger.group(2) ]

#@willie.module.rule(r'(\w+) are ([\w ]+)')
@willie.module.rule(r'([\w ]+) are ([\w ]+)')
def record_are(bot, trigger):
    if trigger.group(1) not in bot.memory['sayings']:
        bot.memory['sayings'][trigger.group(1)] = [ 'are', trigger.group(2) ]

@willie.module.commands('forget')
@willie.module.example('.forget poop')
def forget(bot, trigger):
    if trigger.group(2) in bot.memory['sayings']:
        if trigger.group(2) in bot.memory['sayings_votes_forget']:
            if trigger.nick not in bot.memory['sayings_votes_forget'][trigger.group(2)]:
                response = 'i forgot ' + trigger.group(2) + ' at the behest of ' + bot.memory['sayings_votes_forget'][trigger.group(2)][0] + ' and ' + trigger.nick
                del bot.memory['sayings_votes_forget'][trigger.group(2)]
                del bot.memory['sayings'][trigger.group(2)]
                bot.say(response)
            else:
                response = random.choice([ 'i already heard you say that', 'you already told me that', 'you already said that', 'i saw that already', 'i got that' ])
                bot.reply(response)
        else:
            bot.memory['sayings_votes_forget'][trigger.group(2)] = [ trigger.nick ]
            bot.say('i need 1 more vote to forget ' + trigger.group(2))
    else:
        response = random.choice([ "i don't know anything about", "i didn't have anything for", "i can't match anything for" ])
        bot.reply(response + ' ' + trigger.group(2) + '!')

@willie.module.commands('randomfact')
@willie.module.example('.randomfact')
def randomfact(bot, trigger):
    if len(bot.memory['sayings']) > 0:
        talk_about(bot, random.choice(bot.memory['sayings'].keys()))
    else:
        bot.reply('nothing found!')
