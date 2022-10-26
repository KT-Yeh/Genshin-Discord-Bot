import logging
import discord
import re
import json
from datetime import datetime
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)

def trimCookie(cookie: str) -> str:
    try:
        new_cookie = ' '.join([
            re.search('ltoken=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('ltuid=[0-9]{3,}', cookie).group(),
            re.search('cookie_token=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('account_id=[0-9]{3,}', cookie).group()
        ])
    except:
        new_cookie = None
    return new_cookie

__server_dict = {'os_usa': '美服', 'os_euro': '歐服', 'os_asia': '亞服', 'os_cht': '台港澳服',
    '1': '天空島', '2': '天空島', '5': '世界樹', '6': '美服', '7': '歐服', '8': '亞服', '9': '台港澳服'}
def getServerName(key: str) -> str:
    return __server_dict.get(key)

__weekday_dict = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'}
def getDayOfWeek(time: datetime) -> str:
    delta = time.date() - datetime.now().astimezone().date()
    if delta.days == 0:
        return '今天'
    elif delta.days == 1:
        return '明天'
    return __weekday_dict.get(time.weekday())

def getAppCommandMention(name: str) -> str:
    """取得斜線指令的Mention格式"""
    if not hasattr(getAppCommandMention, 'appcmd_id'):
        try:
            with open('data/app_commands.json', 'r', encoding='utf-8') as f:
                getAppCommandMention.appcmd_id: dict[str, int] = json.load(f)
        except:
            getAppCommandMention.appcmd_id = dict()
    id = getAppCommandMention.appcmd_id.get(name)
    return f"</{name}:{id}>" if id != None else f"`/{name}`"

class EmbedTemplate:
    @staticmethod
    def normal(message: str, **kwargs):
        return discord.Embed(color=0x7289da, description=message, **kwargs)
    
    @staticmethod
    def error(message: str, **kwargs):
        return discord.Embed(color=0xb54031, description=message, **kwargs)