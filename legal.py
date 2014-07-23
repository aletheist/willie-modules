import os
from pymarkovchain import MarkovChain
import willie

def setup(bot):
    mods = bot.config.enumerate_modules()
    for name in mods:
        path = mods[name]
        print 'path: ' + str(path)
    if not bot.memory.contains('legal'):
        if bot.config.core.homedir is not None:
            home_modules_dir = [ bot.config.core.homedir, 'modules' ]
        else:
            home_modules_dir = [ os.path.expanduser('~'), '.willie', 'modules' ]
        with open(os.path.join(home_modules_dir + [ 'legal.txt' ]), 'r') as f:
            legaltext = f.read()
        bot.memory['legal'] = MarkovChain()
        bot.memory['legal'].generateDatabase(legaltext)

@willie.module.commands('legal')
@willie.module.example('.legal')
def legal(bot, trigger):
    reply = ''
    while len(reply) < 150:
        reply = bot.memory['legal'].generateString()
    if reply[-1] != '.':
        reply += '.'
    bot.say(reply)
