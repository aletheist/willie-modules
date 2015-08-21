import random
import sopel

def setup(bot):
    if not bot.memory.contains('8ball_phrases'):
        bot.memory['8ball_phrases'] = ['It is certain', 'It is decidedly so', 'Without a doubt', 'Yes - definitely', 'You may rely on it', 'As I see it, yes', 'Most likely', 'Outlook good', 'Signs point to yes', 'Yes', 'Reply hazy, try again', 'Ask again later', 'Better not tell you now', 'Cannot predict now', 'Concentrate and ask again', 'Don\'t count on it', 'My reply is no', 'My sources say no', 'Outlook not so good', 'Very doubtful']

@sopel.module.commands('8ball', 'mball')
@sopel.module.example('.8ball will Alpha5 ever truly replace WorfBot?')
def ask_magic_8_ball(bot, trigger):
    '''Consults the magic 8 ball for its wisdom.'''
    bot.say('Magic 8 Ball says: ' + random.choice(bot.memory['8ball_phrases']))
