import logging
import genshin
import re
from data.character_names import character_names

__file_handler = logging.FileHandler('data/error.log', encoding='utf-8')
__file_handler.setLevel(logging.WARNING)
__console_handler = logging.StreamHandler()
__console_handler.setLevel(logging.INFO)
__formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')
__file_handler.setFormatter(__formatter)
__console_handler.setFormatter(__formatter)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(__file_handler)
logging.getLogger().addHandler(__console_handler)
log = logging

def getCharacterName(character: genshin.models.BaseCharacter) -> str:
    chinese_name = character_names.get(character.id)
    return chinese_name if chinese_name != None else character.name

def trimCookie(cookie: str) -> str:
    new_cookie = ' '.join([
        re.search('ltoken=[\w]*', cookie).group(),
        re.search('ltuid=[\d]*', cookie).group(),
        re.search('cookie_token=[\w]*', cookie).group(),
        re.search('account_id=[\d]*', cookie).group()
    ])
    return new_cookie