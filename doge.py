import json
import requests
import willie

@willie.module.commands('doge', 'dogecoin')
@willie.module.thread(True)
def bible(bot, trigger):
    '''Look up the current prices from chain.so and average them.'''
    resp = json.loads(requests.get('https://chain.so/api/v2/get_price/DOGE/USD').text)
    prices = [float(p['price']) for p in resp['data']['prices']]
    btcresp = json.loads(requests.get('https://chain.so/api/v2/get_price/DOGE/BTC').text)
    btcprices = [float(p['price']) for p in btcresp['data']['prices']]
    return bot.say('Dogecoin price: ' + str(sum(prices) / len(prices)) + ' USD, ' + str(100000000 * sum(btcprices) / len(btcprices)) + ' Sat')
