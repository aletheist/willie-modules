import re
import json

import sopel
import requests
from bs4 import BeautifulSoup

passage_re = r'(\d*\s*(?:\w+\s+)+\d+(?::\d+(?:-\d+)?)?)\s?(\w+(?:-\w+)?)?'

def setup(bot):
    setup_biblia(bot)
    setup_bibles_org(bot)

def setup_biblia(bot):
    bot.memory['biblia_versions'] = []
    versions_html = requests.get('http://bibliaapi.com/docs/Available_Bibles')
    versions_page = BeautifulSoup(versions_html.text)
    for tr in versions_page.find('table').find_all('tr'):
        if tr.find('th') is None:
            bot.memory['biblia_versions'].append(tr.find_all('td')[0].text.strip())

def setup_bibles_org(bot):
    bot.memory['bibles_versions'] = []
    resp = requests.get('https://bibles.org/v2/versions.js', auth=requests.auth.HTTPBasicAuth('YmAvbTvxEBxzbLedltkKdqun0UPw7GXIYX35fhWD', 'X'))
    resp = json.loads(resp.text)
    for version in resp['response']['versions']:
        bot.memory['bibles_versions'].append(version['id'])

@sopel.module.commands('b', 'bible')
@sopel.module.rule('.*\[%s\]' % passage_re)
@sopel.module.example('.b John 1:1')
@sopel.module.example('.b John 1:1 ESV')
@sopel.module.thread(True)
def bible(bot, trigger):
    '''Look up a passage in the bible. You can specify a desired version.'''
    if trigger.group(1) == 'b' or trigger.group(1) == 'bible':
        if not trigger.group(2):
            return bot.reply('No search term. An example: .b John 1:1')
        else:
            args = re.search(passage_re, trigger.group(2))
    else:
        args = trigger.match

    version = get_version(bot, trigger, args)
    if not version:
        return bot.reply('Specified version not found')

    if version in bot.memory['biblia_versions']:
        lookup_biblia_com(bot, args.group(1), version)
    else:
        lookup_bibles_org(bot, args.group(1), version)

@sopel.module.commands('setbver', 'setbiblever', 'setbeaver')
@sopel.module.example('.setbver ESV')
def set_preferred_version(bot, trigger):
    '''Sets your preferred bible version, to be used in the .b/.bible commands.'''
    if not trigger.group(2):
        get_preferred_version(bot, trigger)
    else:
        version = get_version(bot, trigger, trigger, allow_blank=False)
        if not version:
            return bot.reply('Specified version not found')

        channel_re = re.search(r'^([#&][^\x07\x2C\s]{,200})', trigger.group(2))
        if channel_re is not None and trigger.admin:
            target = channel_re.group(1)
        else:
            target = trigger.nick

        bot.db.set_nick_value(target, 'preferred_versions', version)

        return bot.reply('Set preferred version of ' + target + ' to ' + version)

@sopel.module.commands('getbver', 'getbiblever', 'getbeaver')
def get_preferred_version(bot, trigger):
    return bot.reply('Your preferred version is ' + get_default_version(bot, trigger))

@sopel.module.commands('bver', 'biblever', 'beaver')
@sopel.module.priority('low')
@sopel.module.thread(True)
def get_versions(bot, trigger):
    '''Return a list of bot's Bible versions'''
    versions = ', '.join(sorted(set(bot.memory['biblia_versions'] + bot.memory['bibles_versions'])))
    if not trigger.is_privmsg:
        bot.reply("I am sending you a private message of all my Bible versions!")
    bot.msg(trigger.nick, 'Bible versions I recognise: ' + versions + '.', max_messages=10)

def lookup_bibles_org(bot, passage, version):
    resp = requests.get('https://bibles.org/v2/passages.js', params={ 'q[]': passage, 'version': version }, auth=requests.auth.HTTPBasicAuth('YmAvbTvxEBxzbLedltkKdqun0UPw7GXIYX35fhWD', 'X'))
    resp = json.loads(resp.text)
    if len(resp['response']['search']['result']['passages']) > 0:
        text = resp['response']['search']['result']['passages'][0]['text']

        text = text.replace('\n', '')
        text = re.sub(r'<h\d(?: \w+="[\w\d\.]+")+>.+?</h\d>', '', text)
        text = re.sub(r'<p(?: \w+="[\w\d\.]+")+>', '', text)
        text = re.sub(r'</p>', '', text)
        while re.search(r'<span(?: \w+="[\w\d\.]+")+>(.+?)</span>', text) is not None:
            text = re.sub(r'<span(?: \w+="[\w\d\.]+")+>(.+?)</span>', r'\1', text)

        #copyright = None
        #try:
        #    copyright = resp['response']['search']['result']['passages'][0]['copyright'].lstrip().rstrip().replace('\n', '').replace('<p>', '').replace('</p>', '')
        #except:
        #    pass

        verses = re.split(r'<sup(?: \w+="[\w\d\.-]+")+>[\d-]+</sup>', text)

        verses = [ x for x in verses if x != '' ]

        if len(verses) > 5:
            bot.reply('passage too long')
        else:
            bot.say(resp['response']['search']['result']['passages'][0]['display'] + ' (' + resp['response']['search']['result']['passages'][0]['version_abbreviation'] + ')')
            for verse in verses:
                bot.say(verse)
            #if copyright is not None:
            #    bot.say(copyright)
    else:
        bot.reply('nothing found!')

def lookup_biblia_com(bot, passage, version):
    resp = requests.get('http://api.biblia.com/v1/bible/content/' + version + '.txt', params={ 'passage': passage, 'key': 'fd37d8f28e95d3be8cb4fbc37e15e18e', 'style': 'oneVersePerLine' })
    lines = [ re.sub('^\d+', '', x).strip() for x in resp.text.encode('utf-8').split('\r\n') ]
    if lines == [''] or len(lines) == 1:
        bot.reply('nothing found!')
    else:
        ref = lines[0]
        verses = lines[1:]
        if len(verses) > 5:
            bot.reply('passage too long')
        else:
            bot.say(ref)
            for verse in verses:
                bot.say(verse)

def get_version(bot, trigger, args, allow_blank=True):
    if not args.group(2):
        if allow_blank:
            return get_default_version(bot, trigger)
        else:
            return False
    else:
        if args.group(2) in bot.memory['biblia_versions'] or args.group(2) in bot.memory['bibles_versions']:
            return args.group(2)
        elif 'eng-' + args.group(2) in bot.memory['bibles_versions']:
            return 'eng-' + args.group(2)
        else:
            return False

def get_default_version(bot, trigger):
    if bot.db.get_nick_value(trigger.nick,'preferred_versions'):
        return bot.db.get_nick_value(trigger.nick,'preferred_versions')
    elif bot.db.get_nick_value(trigger.sender,'preferred_versions'):
        return bot.db.get_nick_value(trigger.sender,'preferred_versions')
    else:
        return 'KJV'
