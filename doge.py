import json
import requests

import willie

@willie.module.commands('doge')
@willie.module.thread(True)
def bible(bot, trigger):
    '''Look up the current quoted prices at cryptsy.com, calculate midpoint.'''
    sells = json.loads(requests.get('https://www.cryptsy.com/json.php?file=ajaxsellorderslistv2_182.json').text)
    buys  = json.loads(requests.get('https://www.cryptsy.com/json.php?file=ajaxbuyorderslistv2_182.json').text)
    midpoint = (float(sells['aaData'][0][0]) + float(buys['aaData'][0][0])) / 2.0
    return bot.say('The midpoint of quoted prices is currently $' + str(midpoint))
