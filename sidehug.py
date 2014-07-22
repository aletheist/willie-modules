import willie

@willie.module.commands('sidehug')
@willie.module.example('.sidehug tommles')
def sidehug(bot, trigger):
    if not trigger.group(2):
        target = trigger.nick
    else:
        target = trigger.group(2)
    msg = '\x01ACTION sidehugs %s\x01' % target
    bot.msg(trigger.sender, msg)
