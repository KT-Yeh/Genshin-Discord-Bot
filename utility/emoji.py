import typing
from pathlib import Path

from pydantic import BaseModel


class Notes(BaseModel):
    resin: str = ""
    realm_currency: str = ""
    commission: str = ""
    enemies_of_note: str = ""
    transformer: str = ""
    expedition: str = ""


class Items(BaseModel):
    mora: str = ""
    primogem: str = ""
    intertwined_fate: str = ""


class Emoji(BaseModel):
    notes: Notes = Notes()
    """即時便箋圖示"""
    items: Items = Items()
    """物品圖示"""
    elements: typing.Dict[str, str] = {}
    """原神元素圖示"""
    fightprop: typing.Dict[str, str] = {}
    """角色面板屬性圖示，例：攻擊力、生命值...等"""
    artifact_type: typing.Dict[str, str] = {}
    """聖遺物部位圖示"""
    tcg_dice_cost_elements: typing.Dict[str, str] = {}
    """七聖召喚骰子花費元素類型圖示"""


path = Path("data/emoji.json")
emoji = Emoji.parse_file(path) if path.exists() else Emoji()
