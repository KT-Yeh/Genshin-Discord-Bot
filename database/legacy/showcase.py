import json
import zlib
from typing import Any, Dict, Optional

import aiosqlite


class ShowcaseTable:
    """角色展示櫃資料 Table"""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    async def create(self) -> None:
        """在資料庫新建 Table"""
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS showcase (
                uid int NOT NULL PRIMARY KEY,
                data blob
            )"""
        )
        await self.db.commit()

    async def add(self, uid: int, data: Optional[Dict[str, Any]] = None) -> None:
        """新增使用者到 Table"""
        json_data = json.dumps(data, ensure_ascii=False)
        compressed_data = zlib.compress(json_data.encode(encoding="utf8"), level=5)
        await self.db.execute(
            "INSERT OR REPLACE INTO showcase VALUES(?, ?)", [uid, compressed_data]
        )
        await self.db.commit()

    async def remove(self, uid: int) -> None:
        """從 Table 移除指定的使用者"""
        await self.db.execute("DELETE FROM showcase WHERE uid=?", [uid])
        await self.db.commit()

    async def get(self, uid: int) -> Optional[Dict[str, Any]]:
        """取得指定使用者的資料"""
        async with self.db.execute("SELECT * FROM showcase WHERE uid=?", [uid]) as cursor:
            row = await cursor.fetchone()
            if row is not None:
                data = zlib.decompress(row["data"]).decode(encoding="utf8")
                return json.loads(data)
            return None
