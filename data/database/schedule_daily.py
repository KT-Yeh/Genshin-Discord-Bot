from __future__ import annotations
import aiosqlite
from datetime import date
from typing import Optional, List

class ScheduleDaily:
    id: int
    channel_id: int
    is_mention: bool
    has_honkai: bool
    last_checkin_date: Optional[date]

    def __init__(self, id: int, channel_id: int, *, 
        is_mention: Optional[bool] = None, has_honkai: Optional[bool] = None, last_checkin_date: Optional[date] = None
    ):
        self.id = id
        self.channel_id = channel_id
        self.is_mention = is_mention or False
        self.has_honkai = has_honkai or False
        self.last_checkin_date = last_checkin_date
    
    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> ScheduleDaily:
        return cls(
            id=row['id'],
            channel_id=row['channel_id'],
            is_mention=bool(row['is_mention']),
            has_honkai=bool(row['has_honkai']),
            last_checkin_date=(None if row['last_checkin_date'] == None else date.fromisoformat(row['last_checkin_date']))
        )

class ScheduleDailyTable:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        await self.db.execute('''CREATE TABLE IF NOT EXISTS schedule_daily (
                id int NOT NULL PRIMARY KEY,
                channel_id int NOT NULL,
                is_mention int NOT NULL,
                has_honkai int NOT NULL,
                last_checkin_date text
            )''')
        await self.db.commit()

    async def add(self, user: ScheduleDaily) -> None:
        if (await self.get(user.id)) != None: # 當使用者已存在時
            await self.db.execute('UPDATE schedule_daily SET channel_id=?, is_mention=?, has_honkai=? WHERE id=?',
                [user.channel_id, int(user.is_mention), int(user.has_honkai), user.id])
        else:
            await self.db.execute('INSERT OR REPLACE INTO schedule_daily VALUES(?, ?, ?, ?, ?)',
                [user.id, user.channel_id, int(user.is_mention), int(user.has_honkai), user.last_checkin_date])
        await self.db.commit()
    
    async def remove(self, user_id: int) -> None:
        await self.db.execute('DELETE FROM schedule_daily WHERE id=?', [user_id])
        await self.db.commit()
    
    async def update(self, user_id: int, *, last_checkin_date: bool = False) -> None:
        if last_checkin_date:
            await self.db.execute('UPDATE schedule_daily SET last_checkin_date=? WHERE id=?',
                [date.today().isoformat(), user_id])
        await self.db.commit()

    async def get(self, user_id: int) -> Optional[ScheduleDaily]:
        async with self.db.execute('SELECT * FROM schedule_daily WHERE id=?', [user_id]) as cursor:
            row = await cursor.fetchone()
            return ScheduleDaily.fromRow(row) if row else None

    async def getAll(self) -> List[ScheduleDaily]:
        async with self.db.execute('SELECT * FROM schedule_daily') as cursor:
            rows = await cursor.fetchall()
            return [ScheduleDaily.fromRow(row) for row in rows]

    async def getTotalNumber(self) -> int:
        async with self.db.execute('SELECT COUNT(id) FROM schedule_daily') as cursor:
            row = await cursor.fetchone()
            return row[0]
