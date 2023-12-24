from typing import List, Optional

from pydantic import BaseModel

from .base import GenshinDbBase, GenshinDbListBase


class Parameters(BaseModel):
    """天賦倍率數值"""

    param1: Optional[List[float]] = None
    param2: Optional[List[float]] = None
    param3: Optional[List[float]] = None
    param4: Optional[List[float]] = None
    param5: Optional[List[float]] = None
    param6: Optional[List[float]] = None
    param7: Optional[List[float]] = None
    param8: Optional[List[float]] = None
    param9: Optional[List[float]] = None
    param10: Optional[List[float]] = None
    param11: Optional[List[float]] = None
    param12: Optional[List[float]] = None


class Attributes(BaseModel):
    """天賦詳細屬性、數值"""

    labels: List[str]
    parameters: Parameters
    """天賦倍率數值"""


class Combat(BaseModel):
    name: str
    description: str
    """天賦作用說明"""
    attributes: Attributes
    """天賦詳細屬性、數值"""


class Passive(BaseModel):
    name: str
    description: str


class CostItem(BaseModel):
    name: str
    count: int


class Costs(BaseModel):
    lvl2: List[CostItem]
    lvl3: List[CostItem]
    lvl4: List[CostItem]
    lvl5: List[CostItem]
    lvl6: List[CostItem]
    lvl7: List[CostItem]
    lvl8: List[CostItem]
    lvl9: List[CostItem]
    lvl10: List[CostItem]


class Talent(GenshinDbBase):
    name: str
    """角色名字"""
    combat1: Combat
    """普通攻擊 A"""
    combat2: Combat
    """元素戰技 E"""
    combat3: Combat
    """元素爆發 Q"""
    combatsp: Optional[Combat] = None
    """特殊天賦 (神里、莫娜)"""
    passive1: Passive
    passive2: Passive
    passive3: Optional[Passive] = None
    """生活被動天賦 (旅行者沒有此項目)"""
    costs: Costs
    """升級天賦花費素材"""
    version: str


class Talents(GenshinDbListBase[Talent]):
    __root__: List[Talent]
