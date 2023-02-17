from typing import List, Optional

from pydantic import BaseModel, Field

from .base import GenshinDbBase, GenshinDbListBase


class PartDetail(BaseModel):
    name: str
    relictype: str
    description: str
    story: str


class Images(BaseModel):
    flower_url: Optional[str] = Field(None, alias="flower")
    plume_url: Optional[str] = Field(None, alias="plume")
    sands_url: Optional[str] = Field(None, alias="sands")
    goblet_url: Optional[str] = Field(None, alias="goblet")
    circlet_url: str = Field(alias="circlet")

    flower: Optional[str] = Field(None, alias="nameflower")
    plume: Optional[str] = Field(None, alias="nameplume")
    sands: Optional[str] = Field(None, alias="namesands")
    goblet: Optional[str] = Field(None, alias="namegoblet")
    circlet: str = Field(alias="namecirclet")


class Artifact(GenshinDbBase):
    name: str
    rarity: List[int]
    effect_1pc: Optional[str] = Field(None, alias="1pc")
    effect_2pc: Optional[str] = Field(None, alias="2pc")
    effect_4pc: Optional[str] = Field(None, alias="4pc")

    flower: Optional[PartDetail] = None
    """花"""
    plume: Optional[PartDetail] = None
    """羽"""
    sands: Optional[PartDetail] = None
    """沙"""
    goblet: Optional[PartDetail] = None
    """杯"""
    circlet: PartDetail
    """頭"""

    images: Images
    version: str
    """新增至遊戲當時的版本號碼"""


class Artifacts(GenshinDbListBase[Artifact]):
    __root__: List[Artifact]
