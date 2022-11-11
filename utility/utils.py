import logging
import discord
import genshin
import re
import json
from typing import Optional
from datetime import datetime
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)

async def trimCookie(cookie: str) -> Optional[str]:
    """取得 Cookie 中的 ltoken, ltuid, cookie_token 與 account_id"""
    # 當有 cookie_token 時，取得 ltoken 並延長 cookie_token 的過期時間
    cookie_token = match.group() if (match := re.search('cookie_token=[0-9A-Za-z]{30,}', cookie)) else None
    account_id = match.group() if (match := re.search('account_id=[0-9]{5,}', cookie)) else None
    if cookie_token and account_id:
        new_cookie = await genshin.complete_cookies(f"{cookie_token} {account_id}", refresh=True)
        return ' '.join(f"{key}={value}" for key, value in new_cookie.items())
    
    # 當只有 ltoken 時，直接回傳結果
    ltoken = match.group() if (match := re.search('ltoken=[0-9A-Za-z]{30,}', cookie)) else None
    ltuid = match.group() if (match := re.search('ltuid=[0-9]{5,}', cookie)) else None
    if ltoken and ltuid:
        return ' '.join([ltoken, ltuid])
    
    # 沒有匹配到任何 cookie_token 或 ltoken
    return None

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