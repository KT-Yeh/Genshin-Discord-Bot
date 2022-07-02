import logging
import genshin
import re
import json
from datetime import datetime
from data.game.characters import characters_map
from sentry_sdk.integrations.logging import LoggingIntegration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.CRITICAL
)

def getCharacterName(character: genshin.models.BaseCharacter) -> str:
    chinese_name = None
    if (id := str(character.id)) in characters_map:
        chinese_name = characters_map[id].get('name')
    return chinese_name if chinese_name != None else character.name

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

class UserLastUseTime:
    def __init__(self) -> None:
        try:
            with open('data/last_use_time.json', 'r', encoding="utf-8") as f:
                self.data: dict[str, str] = json.load(f)
        except:
            self.data: dict[str, str]  = { }

    def update(self, user_id: str) -> None:
        """更新使用者最後使用時間"""
        self.data[user_id] = datetime.now().isoformat()
    
    def deleteUser(self, user_id: str) -> None:
        self.data.pop(user_id, None)

    def checkExpiry(self, user_id: str, now: datetime, diff_days: int = 30) -> bool:
        """確認使用者是否超過一定時間沒使用本服務
        param user_id: 使用者Discord ID
        param now: 現在時間
        param diff_days: 相差多少天
        """
        last_time = self.data.get(user_id)
        if last_time == None:
            self.update(user_id)
            return False
        interval = now - datetime.fromisoformat(last_time)
        return True if interval.days > diff_days else False

    def save(self) -> None:
        with open('data/last_use_time.json', 'w', encoding="utf-8") as f:
            json.dump(self.data, f)

user_last_use_time = UserLastUseTime()