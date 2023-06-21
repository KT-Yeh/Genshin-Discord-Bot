from __future__ import annotations

import pickle
import zlib
from typing import Optional, Sequence, Union

import aiosqlite
import genshin


class CharacterData:
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
    artifacts: `Sequence[Artifact]`
        角色裝備的聖遺物
    """

    id: int
    level: int
    friendship: int
    constellation: int
    weapon: Weapon
    artifacts: Sequence[Artifact]

    def __init__(self, character: genshin.models.Character) -> None:
        self.id = character.id
        self.level = character.level
        self.friendship = character.friendship
        self.constellation = character.constellation
        self.weapon = self.Weapon(character.weapon)
        self.artifacts = [self.Artifact(artifact) for artifact in character.artifacts]

    class Weapon:
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
        level: int
        refinement: int

        def __init__(self, weapon: genshin.models.CharacterWeapon) -> None:
            self.id = weapon.id
            self.level = weapon.level
            self.refinement = weapon.refinement

    class Artifact:
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
        pos: int
        level: int

        def __init__(self, artifact: genshin.models.Artifact) -> None:
            self.id = artifact.id
            self.pos = artifact.pos
            self.level = artifact.level


class SpiralAbyssData:
    """深淵紀錄 Table 的資料類別，用來表示使用者某一期的深淵紀錄

    Attributes
    -----
    id: `int`
        使用者 Discord ID
    season: `int`
        深淵期數
    abyss: `SpiralAbyss`
        genshin api 的深淵資料
    characters: `Optional[Sequence[CharacterData]]`
        玩家的角色資料
    """

    id: int
    season: int
    abyss: genshin.models.SpiralAbyss
    characters: Optional[Sequence[CharacterData]] = None

    def __init__(
        self,
        id: int,
        abyss: genshin.models.SpiralAbyss,
        *,
        characters: Union[
            Sequence[genshin.models.Character], Sequence[CharacterData], None
        ] = None,
    ):
        self.id = id
        self.season = abyss.season
        # abyss 完整保存 genshin.py 資料格式，characters 將 genshin.py 的格式轉為自定義格式
        self.abyss = abyss
        if characters is not None:
            self.characters = []
            # 這邊檢查角色是否為 genshin.py 的 Character 型態，若是的話則轉型為 CharacterData
            for c in characters:
                self.characters.append(
                    CharacterData(c) if isinstance(c, genshin.models.Character) else c
                )

    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> SpiralAbyssData:
        abyss: genshin.models.SpiralAbyss = pickle.loads(zlib.decompress(row["abyss"]))
        characters: Optional[Sequence[CharacterData]] = (
            pickle.loads(zlib.decompress(row["characters"]))
            if row["characters"] is not None
            else None
        )
        return cls(row["id"], abyss=abyss, characters=characters)


class SpiralAbyssTable:
    """深淵資料的 Table"""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    async def create(self) -> None:
        """在資料庫新建 Table"""
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS spiral_abyss (
                id int NOT NULL,
                season int NOT NULL,
                abyss blob NOT NULL,
                characters blob,
                PRIMARY KEY (id, season)
            )"""
        )
        await self.db.commit()

    async def add(self, data: SpiralAbyssData) -> None:
        """新增一筆深淵紀錄到 Table"""
        abyss = zlib.compress(pickle.dumps(data.abyss), level=5)
        characters = (
            zlib.compress(pickle.dumps(data.characters), level=5)
            if data.characters is not None
            else None
        )
        await self.db.execute(
            "INSERT OR REPLACE INTO spiral_abyss VALUES(?, ?, ?, ?)",
            [data.id, data.season, abyss, characters],
        )
        await self.db.commit()

    async def remove(self, user_id: int, season: Optional[int] = None) -> None:
        """從 Table 中移除指定的使用者(某一期)的資料"""
        if season:
            await self.db.execute(
                "DELETE FROM spiral_abyss WHERE id=? AND season=?", [user_id, season]
            )
        else:
            await self.db.execute("DELETE FROM spiral_abyss WHERE id=?", [user_id])
        await self.db.commit()

    async def get(self, user_id: int) -> Sequence[SpiralAbyssData]:
        """取得指定使用者的深淵全部期數資料"""
        async with self.db.execute(
            "SELECT * FROM spiral_abyss WHERE id=? ORDER BY season DESC", [user_id]
        ) as cursor:
            rows = await cursor.fetchall()
            return [SpiralAbyssData.fromRow(row) for row in rows]
