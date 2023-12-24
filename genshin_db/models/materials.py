from typing import List, Optional

from pydantic import BaseModel, Field, validator

from .base import GenshinDbBase, GenshinDbListBase


class Images(BaseModel):
    icon: str = Field(alias="filename_icon")


class Material(GenshinDbBase):
    name: str
    description: str
    rarity: Optional[int] = None
    category: str
    material_type: str = Field(alias="typeText")
    sources: List[str]
    """獲取來源"""
    images: Images

    drop_domain: Optional[str] = Field(None, alias="dropdomain")
    """培養素材的掉落秘境"""
    days_of_week: Optional[List[str]] = Field(None, alias="daysofweek")
    """秘境開放日"""
    dupealias: Optional[str] = None
    """當物品名字重複時的編號別名"""
    version: Optional[str] = None
    """新增至遊戲當時的版本號碼"""

    @validator("version", pre=True)
    def remove_empty_version(cls, v: str) -> Optional[str]:
        return None if v == "" else v


class Materials(GenshinDbListBase[Material]):
    __root__: List[Material]
