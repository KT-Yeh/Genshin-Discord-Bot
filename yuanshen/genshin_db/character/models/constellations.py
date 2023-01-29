from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ConstellationDetail(BaseModel):
    name: str
    effect: str


class Images(BaseModel):
    c1_url: str = Field(alias="c1")
    c2_url: str = Field(alias="c2")
    c3_url: str = Field(alias="c3")
    c4_url: str = Field(alias="c4")
    c5_url: str = Field(alias="c5")
    c6_url: str = Field(alias="c6")

    constellation: str
    constellation2: Optional[str] = None


class Constellation(BaseModel):
    name: str
    """角色名稱"""
    c1: ConstellationDetail
    c2: ConstellationDetail
    c3: ConstellationDetail
    c4: ConstellationDetail
    c5: ConstellationDetail
    c6: ConstellationDetail
    images: Images
    version: str


class Constellations(BaseModel):
    __root__: List[Constellation]
