import aiosqlite
import json
from typing import Optional, Dict, Any

class ShowcaseTable:
    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    async def create(self) -> None:
        await self.db.execute('''CREATE TABLE IF NOT EXISTS showcase (
                uid int NOT NULL UNIQUE,
                data text
            )''')
        await self.db.commit()

    async def add(self, uid: int, data: Dict[str, Any] = None) -> None:
        json_data = json.dumps(data, ensure_ascii=False)
        await self.db.execute('INSERT OR REPLACE INTO showcase VALUES(?, ?)',
            [uid, json_data])
        await self.db.commit()

    async def remove(self, uid: int) -> None:
        await self.db.execute('DELETE FROM showcase WHERE uid=?', [uid])
        await self.db.commit()
    
    async def get(self, uid: int) -> Optional[Dict[str, Any]]:
        async with self.db.execute('SELECT * FROM showcase WHERE uid=?', [uid]) as cursor:
            row = await cursor.fetchone()
            if row != None:
                return json.loads(row['data'])
            return None