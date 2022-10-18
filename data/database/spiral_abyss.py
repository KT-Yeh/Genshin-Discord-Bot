import aiosqlite
import pickle
import zlib
from typing import Sequence, Optional
from genshin.models import SpiralAbyss, PartialCharacter

class SpiralAbyssData:
    def __init__(self, id: int = None, *, season: int = None, abyss: SpiralAbyss = None, characters: Sequence[PartialCharacter] = None):
        self.id = id
        self.season = season or (abyss.season if abyss != None else -1)
        self.abyss = abyss
        self.characters = characters

    @classmethod
    def fromRow(cls, row: aiosqlite.Row):
        abyss = pickle.loads(zlib.decompress(row['abyss'])) if row['abyss'] != None else None
        characters = pickle.loads(zlib.decompress(row['characters'])) if row['characters'] != None else None
        try:
            return cls(row['id'], season=row['season'], abyss=abyss, characters=characters)
        except:
            return cls()

class SpiralAbyssTable:
    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    async def create(self) -> None:
        await self.db.execute('''CREATE TABLE IF NOT EXISTS spiral_abyss (
                id int NOT NULL,
                season int NOT NULL,
                abyss blob,
                characters blob,
                PRIMARY KEY (id, season)
            )''')
        await self.db.commit()

    async def add(self, data: SpiralAbyssData) -> None:
        abyss = zlib.compress(pickle.dumps(data.abyss), level=5) if data.abyss != None else None
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