import re
import json

import sopel
import requests
from bs4 import BeautifulSoup

PASSAGE_RE = r'(\d*\s*(?:\w+\s+)+\d+(?::\d+(?:-\d+)?)?)\s?(\w+(?:-\w+)?)?'
BIBLES_ORG_BASE = 'http://bibles.org/'
MAX_RETURN_LINES = 5

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
    resp = requests.get('http://m.bibles.org/eng-GNTD/John/1/1/compare')
    page = BeautifulSoup(resp.text)

    version_list = page.find('ul', id='whichVersionList')
    for li in version_list.find_all('li'):
        for inp in li.find_all('input'):
            if inp['name'] == 'version[]' and inp['value'][:4] == 'eng-':
                bot.memory['bibles_versions'].append(inp['value'])

@sopel.module.commands('b', 'bible')
@sopel.module.rule('.*\[%s\]' % PASSAGE_RE)
@sopel.module.example('.b John 1:1')
@sopel.module.example('.b John 1:1 ESV')
@sopel.module.thread(True)
def bible(bot, trigger):
    '''Look up a passage in the bible. You can specify a desired version.'''

    try:
        if trigger.group(1) == 'b' or trigger.group(1) == 'bible':
            if not trigger.group(2):
                raise NoSearchTermException
            else:
                args = re.search(PASSAGE_RE, trigger.group(2))
        else:
            args = trigger.match

        if args is None:
            raise NoSearchTermException

        passage = args.group(1)
        if infer_verse_count_from_reference(passage) > MAX_RETURN_LINES:
            raise PassageTooLongException
        if not reference_makes_sense(passage):
            raise NonsensicalReferenceException

        version = get_version(bot, trigger, args)
        if not version:
            raise VersionNotFoundException

        cmd = lookup_biblia_com if version in bot.memory['biblia_versions'] else lookup_bibles_org
        cmd(bot, passage, version)
    except NothingFoundException:
        bot.reply('Nothing found!')
    except NoSearchTermException:
        bot.reply('No search term. An example: .b John 1:1')
    except NonsensicalReferenceException:
        bot.reply('Reference does not make sense')
    except PassageTooLongException:
        bot.reply('Passage too long')
    except VersionNotFoundException:
        bot.reply('Specified version not found')

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

        return bot.reply('Set preferred version of ' + target + ' to ' + filter_language_prefix(version))

@sopel.module.commands('getbver', 'getbiblever', 'getbeaver')
def get_preferred_version(bot, trigger):
    return bot.reply('Your preferred version is ' + filter_language_prefix(get_default_version(bot, trigger)))

@sopel.module.commands('bver', 'biblever', 'beaver')
@sopel.module.priority('low')
@sopel.module.thread(True)
def get_versions(bot, trigger):
    '''Return a list of bot's Bible versions'''
    versions = ', '.join(sorted(set(bot.memory['biblia_versions'] + bot.memory['bibles_versions'])))
    if not trigger.is_privmsg:
        bot.reply("I am sending you a private message of all my Bible versions!")
    bot.msg(trigger.nick, 'Bible versions I recognize:')
    bot.msg(trigger.nick, 'From biblia.com: ' + ', '.join(sorted(list_omit_if_language_prefix(bot.memory['biblia_versions']))) + '.', max_messages=MAX_RETURN_LINES)
    bot.msg(trigger.nick, 'From bibles.org: ' + ', '.join(sorted(list_filter_language_prefix(bot.memory['bibles_versions']))) + '.', max_messages=MAX_RETURN_LINES)

def lookup_bibles_org(bot, passage, version):
    resp = requests.get(BIBLES_ORG_BASE + version + '/passages.json', params={ 'q[]': passage })
    resp = json.loads(resp.text)

    if len(resp['passages']) == 0:
        raise NothingFoundException

    passage_id   = resp['passages'][0]['id']
    verses_range = [ int(x) for x in resp['passages'][0]['url'].split('/')[-1].split('-') ]
    book_abbrev  = passage_id.split('.')[0].split(':')[1]
    chapter_num  = passage_id.split('.')[1]
    reference    = resp['passages'][0]['reference']
    if infer_verse_count_from_reference(reference) > MAX_RETURN_LINES:
        raise PassageTooLongException
    version_api  = passage_id.split('.')[0].split(':')[0].split('-')[1]

    if len(verses_range) > 1:
        verses_range = range(verses_range[0], verses_range[1] + 1)

    resp = requests.get(BIBLES_ORG_BASE + 'chapters/' + passage_id + '.json')
    resp = json.loads(resp.text)

    page = BeautifulSoup(resp['text'])
    span_ref_base = page.find('span', { 'class': re.compile('v\d+') }).attrs['class'][0].split('_')[0]

    verses = []

    for v_num in verses_range:
        span_class = '_'.join([ span_ref_base, chapter_num, str(v_num) ])
        spans = page.findAll('span', { 'class': span_class })
        if len(spans) > 0:
            verse_parts = []
            for span in spans:
                [ x.extract() for x in span.findAll('sup') ]
                [ x.extract() for x in span.findAll('a', { 'class': 'notelink' }) ]
                [ verse_parts.append(x) for x in span.stripped_strings ]
            verses.append(' '.join(verse_parts))

    if len(verses) > MAX_RETURN_LINES:
        raise PassageTooLongException

    bot.say(reference + ' (' + version_api + ')')
    for verse in verses:
        bot.say(verse)

def lookup_biblia_com(bot, passage, version):
    resp = requests.get('http://api.biblia.com/v1/bible/content/' + version + '.txt', params={ 'passage': passage, 'key': 'fd37d8f28e95d3be8cb4fbc37e15e18e', 'style': 'oneVersePerLine' })
    lines = [ re.sub('^\d+', '', x).strip() for x in resp.text.encode('utf-8').split('\r\n') ]
    if lines == [''] or len(lines) == 1:
        raise NothingFoundException

    ref = lines[0]
    verses = lines[1:]
    if len(verses) > MAX_RETURN_LINES:
        raise PassageTooLongException

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
        req_version = args.group(2).upper()
        if req_version in bot.memory['biblia_versions'] or req_version in bot.memory['bibles_versions']:
            return req_version
        elif 'eng-' + req_version in bot.memory['bibles_versions']:
            return 'eng-' + req_version
        else:
            return False

def get_default_version(bot, trigger):
    if bot.db.get_nick_value(trigger.nick,'preferred_versions'):
        return bot.db.get_nick_value(trigger.nick,'preferred_versions')
    elif bot.db.get_nick_value(trigger.sender,'preferred_versions'):
        return bot.db.get_nick_value(trigger.sender,'preferred_versions')
    else:
        return 'KJV'

def infer_verse_count_from_reference(reference):
    if len(reference.split(':')) > 1:
        verse_part = reference.split(':')[1]
        if len(verse_part.split('-')) > 1:
            verse_range = [ int(x) for x in verse_part.split('-') ]
            return verse_range[1] - verse_range[0] + 1
    return 0

def reference_makes_sense(reference):
    if len(reference.split(':')) > 1:
        verse_part = reference.split(':')[1]
        if len(verse_part.split('-')) > 1:
            verse_range = [ int(x) for x in verse_part.split('-') ]
            if verse_range[1] <= verse_range[0]:
                return False
    return True

def filter_language_prefix(x):
    return x.split('-')[1] if x.find('-') != -1 else x

def list_filter_language_prefix(l):
    return [ x.split('-')[1] for x in l ]

def list_omit_if_language_prefix(l):
    return [ x for x in l if x.find('-') == -1 ]

class NothingFoundException(Exception):
    pass

class NoSearchTermException(Exception):
    pass

class NonsensicalReferenceException(Exception):
    pass

class PassageTooLongException(Exception):
    pass

class VersionNotFoundException(Exception):
    pass
