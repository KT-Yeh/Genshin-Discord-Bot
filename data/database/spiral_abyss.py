from __future__ import annotations
import aiosqlite
import pickle
import zlib
from typing import Sequence, Optional
from genshin.models import SpiralAbyss, PartialCharacter

class SpiralAbyssData:
    id: int
    season: int
    abyss: SpiralAbyss
    characters: Optional[Sequence[PartialCharacter]]
    
    def __init__(self, id: int, abyss: SpiralAbyss, *, characters: Optional[Sequence[PartialCharacter]] = None):
        self.id = id
        self.season = abyss.season
        self.abyss = abyss
        self.characters = characters

    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> SpiralAbyssData:
        abyss: SpiralAbyss = pickle.loads(zlib.decompress(row['abyss']))
        characters: Optional[Sequence[PartialCharacter]] = pickle.loads(zlib.decompress(row['characters'])) if row['characters'] != None else None
        return cls(row['id'], abyss=abyss, characters=characters)

class SpiralAbyssTable:
    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    async def create(self) -> None:
        await self.db.execute('''CREATE TABLE IF NOT EXISTS spiral_abyss (
                id int NOT NULL,
                season int NOT NULL,
                abyss blob NOT NULL,
                characters blob,
                PRIMARY KEY (id, season)
            )''')
        await self.db.commit()

    async def add(self, data: SpiralAbyssData) -> None:
        abyss = zlib.compress(pickle.dumps(data.abyss), level=5)
        characters = zlib.compress(pickle.dumps(data.characters), level=5) if data.characters != None else None
        await self.db.execute('INSERT OR REPLACE INTO spiral_abyss VALUES(?, ?, ?, ?)',
            [data.id, data.season, abyss, characters])
        await self.db.commit()

    async def remove(self, user_id: int, season: Optional[int] = None) -> None:
        if season:
            await self.db.execute('DELETE FROM spiral_abyss WHERE id=? AND season=?', [user_id, season])
        else:
            await self.db.execute('DELETE FROM spiral_abyss WHERE id=?', [user_id])
        await self.db.commit()
    
    async def get(self, user_id: int) -> Sequence[SpiralAbyssData]:
        async with self.db.execute('SELECT * FROM spiral_abyss WHERE id=? ORDER BY season DESC', [user_id]) as cursor:
            rows = await cursor.fetchall()
            return [SpiralAbyssData.fromRow(row) for row in rows]