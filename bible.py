import re
import json

import willie
import requests

def setup(bot):
    if not bot.memory.contains('preferred_versions'):
        bot.memory['preferred_versions'] = willie.tools.WillieMemory()

@willie.module.commands('b', 'bible')
@willie.module.rule(r'.*\[(.+)\]')
@willie.module.example('.b John 1:1')
@willie.module.example('.b John 1:1 ESV')
def bible(bot, trigger):
    '''Look up a passage in the bible. You can specify a desired version.'''
    brackets = True
    passage = trigger.group(1) # Either the command (b or bible), or the capture group from the rule.
    if passage == 'b' or passage == 'bible':
        if not trigger.group(2):
            return bot.reply('No search term. An example: .b John 1:1')
        else:
            passage = trigger.group(2)
            brackets = False
    version_re = re.search(r' ([a-z]+-)?([A-Z]+)$', passage)
    if version_re is not None:
        if version_re.group(1) is None:
            version = 'eng-' + version_re.group(2)
        else:
            version = ''.join(version_re.groups())
        passage = passage.replace(version_re.group(0), '')
    else:
        if trigger.nick in bot.memory['preferred_versions']:
            version = bot.memory['preferred_versions'][trigger.nick]
        elif trigger.sender in bot.memory['preferred_versions']:
            version = bot.memory['preferred_versions'][trigger.sender]
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


        copyright = None
        try:
            copyright = resp['response']['search']['result']['passages'][0]['copyright'].lstrip().rstrip().replace('\n', '').replace('<p>', '').replace('</p>', '')
        except:
            pass

        verses = re.split(r'<sup(?: \w+="[\w\d\.-]+")+>[\d-]+</sup>', text)

        verses = [ x for x in verses if x != '' ]

        if len(verses) > 5:
            bot.reply('passage too long')
        else:
            bot.say(resp['response']['search']['result']['passages'][0]['display'] + ' (' + resp['response']['search']['result']['passages'][0]['version_abbreviation'] + ')')
            for verse in verses:
                bot.say(verse)
            if copyright is not None:
                bot.say(copyright)
    else:
        if not brackets:
            bot.reply('nothing found!')


@willie.module.commands('bver', 'biblever')
@willie.module.example('.bver ESV')
def set_preferred_version(bot, trigger):
    '''Sets your preferred bible version, to be used in the .b/.bible commands.'''
    arg = trigger.group(2)
    version_re = re.search(r'([a-z]+-)?([A-Z]+)$', arg)
    if version_re is None:
        return bot.reply('No version specified!')

    if version_re.group(1) is None:
        version = 'eng-' + version_re.group(2)
    else:
        version = ''.join(version_re.groups())

    target = trigger.nick
    channel_re = re.search(r'^([#&][^\x07\x2C\s]{,200})', arg)
    if channel_re is not None and trigger.admin:
        target = channel_re.group(1)

    bot.memory['preferred_versions'][target] = version

    return bot.reply('Set preferred version of ' + target + ' to ' + version)
