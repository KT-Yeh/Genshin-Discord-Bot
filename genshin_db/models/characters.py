from typing import List, Optional

from pydantic import BaseModel, Field, validator

from ..api import API
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
    filename_icon: str
    filename_gachaSplash: Optional[str] = None

    @property
    def icon_url(self) -> str:
        return API.get_image_url(self.filename_icon)

    @property
    def cover1_url(self) -> str | None:
        if self.filename_gachaSplash is None:
            return None
        return API.get_image_url(self.filename_gachaSplash)


class Character(GenshinDbBase):
    name: str
    title: Optional[str] = None
    """卡池稱號"""
    description: str
    rarity: int
    element: Element = Field(alias="elementText")
    weapontype: str = Field(alias="weaponText")
    substat: str = Field(alias="substatText")
    """突破加成屬性"""

    gender: str
    region: Optional[str] = None
    affiliation: Optional[str] = None
    birthdaymmdd: Optional[str] = None
    birthday: Optional[str] = None

    constellation: str
    """命之座名稱"""
    character_voice: CharacterVoice = Field(alias="cv")
    ascend_costs: AscendCosts = Field(alias="costs")
    """突破所需素材"""
    images: Optional[Images] = None
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
