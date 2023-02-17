from typing import List, Optional

from pydantic import BaseModel, Field

from .base import GenshinDbBase, GenshinDbListBase


class Cooking(BaseModel):
    effect: str
    description: str


class Ingredient(BaseModel):
    name: str
    count: int


class Images(BaseModel):
    icon: str = Field(alias="nameicon")


class Food(GenshinDbBase):
    name: str
    rarity: int
    food_type: str = Field(alias="foodfilter")
    """冒險類、恢復類、攻擊類、防禦類料理"""
    description: str

    effect: str
    suspicious: Optional[Cooking] = None
    """失敗料理"""
    normal: Optional[Cooking] = None
    """普通料理"""
    delicious: Optional[Cooking] = None
    """完美料理"""

    ingredients: List[Ingredient]
    images: Images
    version: str
    """新增至遊戲當時的版本號碼"""
    basedish: Optional[str] = None
    """角色特色料理是基於哪一道料理"""
    character: Optional[str] = None
    """角色特色料理的角色名字"""


class Foods(GenshinDbListBase[Food]):
    __root__: List[Food]
