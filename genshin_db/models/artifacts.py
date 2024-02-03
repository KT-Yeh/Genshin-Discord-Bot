from typing import List, Optional

from pydantic import BaseModel, Field

from ..api import API
from .base import GenshinDbBase, GenshinDbListBase


class PartDetail(BaseModel):
    name: str
    relictype: str = Field(alias="relicText")
    description: str
    story: str


class Images(BaseModel):
    filename_flower: Optional[str]
    filename_plume: Optional[str]
    filename_sands: Optional[str]
    filename_goblet: Optional[str]
    filename_circlet: str

    @property
    def flower_url(self) -> Optional[str]:
        return None if self.filename_flower is None else API.get_image_url(self.filename_flower)

    @property
    def plume_url(self) -> Optional[str]:
        return None if self.filename_plume is None else API.get_image_url(self.filename_plume)

    @property
    def sands_url(self) -> Optional[str]:
        return None if self.filename_sands is None else API.get_image_url(self.filename_sands)

    @property
    def goblet_url(self) -> Optional[str]:
        return None if self.filename_goblet is None else API.get_image_url(self.filename_goblet)

    @property
    def circlet_url(self) -> str:
        return API.get_image_url(self.filename_circlet)


class Artifact(GenshinDbBase):
    name: str
    rarity: List[int] = Field(alias="rarityList")
    effect_1pc: Optional[str] = Field(None, alias="effect1Pc")
    effect_2pc: Optional[str] = Field(None, alias="effect2Pc")
    effect_4pc: Optional[str] = Field(None, alias="effect4Pc")

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
