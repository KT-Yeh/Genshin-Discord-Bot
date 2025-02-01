from pydantic import BaseModel


class Weapon(BaseModel):
    """武器資料

    Attributes
    -----
    id: `int`
        武器 ID
    level: `int`
        武器等級
    refinement: `int`
        武器精煉
    """

    id: int
    """武器 ID"""
    level: int
    """武器等級"""
    refinement: int
    """武器精煉"""

    class Config:
        orm_mode = True


class Artifact(BaseModel):
    """聖遺物資料

    Attributes
    -----
    id: `int`
        聖遺物 ID
    pos: `int`
        聖遺物裝備位置
    level: `int`
        聖遺物等級
    """

    id: int
    """聖遺物 ID"""
    pos: int
    """聖遺物裝備位置"""
    level: int
    """聖遺物等級"""

    class Config:
        orm_mode = True


class CharacterData(BaseModel):
    """自定義欲保存在資料庫的深淵角色資料

    Attributes
    -----
    id: `int`
        角色 ID
    level: `int`
        角色等級
    friendship: `int`
        角色好感等級
    constellation: `int`
        角色命之座
    weapon: `Weapon`
        角色裝備的武器
    artifacts: `list[Artifact] | None = None`
        角色裝備的聖遺物
    """

    id: int
    """角色 ID"""
    level: int
    """角色等級"""
    friendship: int
    """角色好感等級"""
    constellation: int
    """角色命之座"""
    weapon: Weapon
    """角色裝備的武器"""
    artifacts: list[Artifact] | None = None
    """角色裝備的聖遺物"""

    class Config:
        orm_mode = True
