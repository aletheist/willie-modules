import re

import sopel
import requests
from bs4 import BeautifulSoup

def first_sibling_matching(el, name):
    for element in el.next_elements:
        if element.name == name:
            return element

@sopel.module.commands('fallacy')
@sopel.module.example('.fallacy Ad Hominem')
def fallacy(bot, trigger):
    if not trigger.group(2):
        return
    fallacy = trigger.group(2).lower().replace(' ', '-')
    
    resp = requests.get('http://www.nizkor.org/features/fallacies/' + fallacy + '.html')
    if resp.status_code != 200:
        bot.reply('nothing found!')
    else:
        page = BeautifulSoup(resp.text)

        p_desc_text = first_sibling_matching(page.find('h4'), 'p').text
        ol_desc = first_sibling_matching(page.find('h4'), 'ol')

        p_desc_text = re.sub('\n\n$', '', p_desc_text)
        p_desc_text = re.sub('\n', ' ', p_desc_text)

        ol_texts = [ str(i + 1) + '. ' + x for i, x in enumerate(ol_desc.stripped_strings) ]

        bot.say(p_desc_text)
        for ol_text in ol_texts:
            bot.say(ol_text)
