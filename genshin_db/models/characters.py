from typing import List, Optional

from pydantic import BaseModel, Field, validator

from .base import GenshinDbBase, GenshinDbListBase
from .enums import Element


class CharacterVoice(BaseModel):
    english: str
    chinese: str
    japanese: str
    korean: str


class AscendItem(BaseModel):
    name: str
    count: int


class AscendCosts(BaseModel):
    ascend1: List[AscendItem]
    ascend2: List[AscendItem]
    ascend3: List[AscendItem]
    ascend4: List[AscendItem]
    ascend5: List[AscendItem]
    ascend6: List[AscendItem]


class Images(BaseModel):
    icon_url: str = Field(alias="icon")
    sideicon_url: str = Field(alias="sideicon")
    cover1_url: Optional[str] = Field(None, alias="cover1")
    cover2_url: Optional[str] = Field(None, alias="cover2")

    icon: str = Field(alias="nameicon")
    iconcard: str = Field(alias="nameiconcard")
    sideicon: str = Field(alias="namesideicon")
    gachasplash: Optional[str] = Field(None, alias="namegachasplash")
    gachaslice: Optional[str] = Field(None, alias="namegachaslice")


class Character(GenshinDbBase):
    name: str
    title: Optional[str] = None
    """卡池稱號"""
    description: str
    rarity: int
    element: Element
    weapontype: str
    substat: str
    """突破加成屬性"""

    gender: str
    body: str
    region: Optional[str] = None
    affiliation: Optional[str] = None
    birthdaymmdd: Optional[str] = None
    birthday: Optional[str] = None

    constellation: str
    """命之座名稱"""
    character_voice: CharacterVoice = Field(alias="cv")
    ascend_costs: AscendCosts = Field(alias="costs")
    """突破所需素材"""
    images: Images
    version: str
    """新增至遊戲當時的版本號碼"""

    @validator("*", pre=True)
    def empty_string_to_none(cls, v):
        return None if v == "" else v

    @validator("name", pre=True)
    def modify_traveller_name(cls, v: str) -> str:
        if v == "空" or v == "熒":
            return f"旅行者 ({v})"
        return v


class Characters(GenshinDbListBase[Character]):
    __root__: List[Character]
