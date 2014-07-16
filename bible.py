import re
import json

import willie
import requests

def setup(bot):
    if not bot.memory.contains('preferred_versions'):
        bot.memory['preferred_versions'] = willie.tools.WillieMemory()

@willie.module.commands('b', 'bible')
@willie.module.example('.b John 1:1')
def bible(bot, trigger):
    if not trigger.group(2):
        return bot.reply('No search term. An example: .b John 1:1')
    passage = trigger.group(2)
    version_re = re.search(r' ([a-z]+-)?([A-Z]+)$', passage)
    if version_re is not None:
        if version_re.group(1) is None:
            version = 'eng-' + version_re.group(2)
        else:
            version = ''.join(version_re.groups())
        bot.memory['preferred_versions'][trigger.nick] = version
        passage = passage.replace(version_re.group(0), '')
    else:
        if trigger.nick in bot.memory['preferred_versions']:
            version = bot.memory['preferred_versions'][trigger.nick]
        else:
            version = 'eng-KJVA'
    resp = requests.get('https://bibles.org/v2/passages.js', params={ 'q[]': passage, 'version': version }, auth=requests.auth.HTTPBasicAuth('YmAvbTvxEBxzbLedltkKdqun0UPw7GXIYX35fhWD', 'X'))
    resp = json.loads(resp.text)
    if len(resp['response']['search']['result']['passages']) > 0:
        text = resp['response']['search']['result']['passages'][0]['text']

        text = text.replace('\n', '')
        text = re.sub(r'<h\d(?: \w+="[\w\d\.]+")+>.+?</h\d>', '', text)
        text = re.sub(r'<p(?: \w+="[\w\d\.]+")+>', '', text)
        text = re.sub(r'</p>', '', text)
        text = re.sub(r'<span(?: \w+="[\w\d\.]+")+>(.+?)</span>', r'\1', text)

        verses = re.split(r'<sup(?: \w+="[\w\d\.-]+")+>[\d-]+</sup>', text)

        verses = [ x for x in verses if x != '' ]

        if len(verses) > 5:
            bot.reply('passage too long')
        else:
            bot.say(resp['response']['search']['result']['passages'][0]['display'] + ' (' + resp['response']['search']['result']['passages'][0]['version_abbreviation'] + ')')
            for verse in verses:
                bot.say(verse)
    else:
        bot.reply('nothing found!')
