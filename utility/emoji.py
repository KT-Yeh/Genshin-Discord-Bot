import typing
from pathlib import Path
from pydantic import BaseModel

class Notes(BaseModel):
    resin: str = ''
    realm_currency: str = ''
    commission: str = ''
    enemies_of_note: str = ''
    transformer: str = ''

class Items(BaseModel):
    mora: str = ''
    primogem: str = ''
    intertwined_fate: str = ''

class Emoji(BaseModel):
    notes: Notes = Notes()
    items: Items = Items()
    elements: typing.Dict[str, str] = { }
    fightprop: typing.Dict[str, str] = { }
    artifact_type: typing.Dict[str, str] = { }

path = Path('data/emoji.json')
emoji = Emoji.parse_file(path) if path.exists() else Emoji()