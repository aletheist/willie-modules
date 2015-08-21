import re
import datetime
import dns.resolver

import sopel
import requests

def setup(bot):
    if not bot.memory.contains('country_zz_zone'):
        bot.memory['country_zz_zone'] = sopel.tools.SopelMemory()
        zz_text = requests.get('http://countries.nerd.dk/isolist.txt').text
        for match in re.findall('([a-z]{2})\s+(\d+\.\d+\.\d+\.\d+)', zz_text):
            bot.memory['country_zz_zone'][match[1]] = match[0]
    if not bot.memory.contains('country_iso_3166'):
        bot.memory['country_iso_3166'] = sopel.tools.SopelMemory()
        iso_text = requests.get('http://www.combit.net/de/support/files/cmbtkb/country_names_and_code_elements.txt').text.encode('utf-8')
        for match in re.findall('(.+?);([A-Z]{2})', iso_text):
            if match[0] != 'Country Name':
                bot.memory['country_iso_3166'][match[1].lower()] = match[0]
    if not bot.memory.contains('country_ip_cache'):
        bot.memory['country_ip_cache'] = sopel.tools.SopelMemory()
    if not bot.memory.contains('country_host_timestamp'):
        bot.memory['country_host_timestamp'] = sopel.tools.SopelMemory()

@sopel.module.event('JOIN')
@sopel.module.rule('.*')
def country(bot, trigger):
    if trigger.host in bot.memory['country_host_timestamp'] and (datetime.datetime.now() - bot.memory['country_host_timestamp'][trigger.host]).total_seconds() < 30:
        return

    bot.memory['country_host_timestamp'][trigger.host] = datetime.datetime.now()
    ip = None
    m = re.search('ip.(\d+\.\d+\.\d+\.\d+)$', trigger.host)
    if m is None:
        try:
            # have to look up IP address for hostname
            ip = dns.resolver.query(trigger.host, 'A')[0].address
        except dns.resolver.NXDOMAIN:
            pass
        except dns.resolver.NoAnswer:
            pass
    else:
        ip = m.group(1)

    country = 'an undisclosed location'
    if ip is not None:
        if ip in bot.memory['country_ip_cache']:
            country = bot.memory['country_ip_cache'][ip]
        else:
            zz_ip = dns.resolver.query(reverse_ip(ip) + '.zz.countries.nerd.dk', 'A')[0].address
            if zz_ip in bot.memory['country_zz_zone']:
                country_code = bot.memory['country_zz_zone'][zz_ip]
                if country_code in bot.memory['country_iso_3166']:
                    country = bot.memory['country_iso_3166'][country_code]
                    bot.memory['country_ip_cache'][ip] = country
    bot.notice('A wild ' + trigger.nick + ' arrives from ' + country + '!', '@' + trigger.sender)

def reverse_ip(ip):
    return '.'.join(ip.split('.')[::-1])
