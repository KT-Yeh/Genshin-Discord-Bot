import logging
import genshin
import re
from data.character_names import character_names

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
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