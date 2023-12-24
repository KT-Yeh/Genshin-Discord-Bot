from typing import List

from pydantic import BaseModel

from .base import GenshinDbBase, GenshinDbListBase


class ConstellationDetail(BaseModel):
    name: str
    description: str


class Constellation(GenshinDbBase):
    name: str
    """角色名字"""
    c1: ConstellationDetail
    c2: ConstellationDetail
    c3: ConstellationDetail
    c4: ConstellationDetail
    c5: ConstellationDetail
    c6: ConstellationDetail
    version: str


class Constellations(GenshinDbListBase[Constellation]):
    __root__: List[Constellation]
