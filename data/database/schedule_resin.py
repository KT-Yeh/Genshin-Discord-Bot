from __future__ import annotations
import aiosqlite
from datetime import datetime
from typing import Optional, List

class ScheduleResin:
    id: int
    channel_id: int
    next_check_time: Optional[datetime]
    threshold_resin: Optional[int]
    threshold_currency: Optional[int]
    threshold_transformer: Optional[int]
    threshold_expedition: Optional[int]
    check_commission_time: Optional[datetime]

    def __init__(self, id: int, channel_id: int, *,
                 next_check_time: Optional[datetime] = None,
                 threshold_resin: Optional[int] = None,
                 threshold_currency: Optional[int] = None,
                 threshold_transformer: Optional[int] = None,
                 threshold_expedition: Optional[int] = None,
                 check_commission_time: Optional[datetime] = None):
        self.id= id
        self.channel_id = channel_id
        self.next_check_time = next_check_time
        self.threshold_resin = threshold_resin
        self.threshold_currency = threshold_currency
        self.threshold_transformer = threshold_transformer
        self.threshold_expedition = threshold_expedition
        self.check_commission_time = check_commission_time
    
    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> ScheduleResin:
        return cls(
            id=row['id'],
            channel_id=row['channel_id'],
            next_check_time=(datetime.fromisoformat(row['next_check_time']) if row['next_check_time'] else None),
            threshold_resin=row['threshold_resin'],
            threshold_currency=row['threshold_currency'],
            threshold_transformer=row['threshold_transformer'],
            threshold_expedition=row['threshold_expedition'],
            check_commission_time=(datetime.fromisoformat(row['check_commission_time']) if row['check_commission_time'] else None)
        )

class ScheduleResinTable:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        await self.db.execute('''CREATE TABLE IF NOT EXISTS schedule_resin (
                id int NOT NULL PRIMARY KEY,
                channel_id int NOT NULL,
                next_check_time text,
                threshold_resin int,
                threshold_currency int,
                threshold_transformer int,
                threshold_expedition int,
                check_commission_time text
            )''')
        await self.db.commit()

    async def add(self, user: ScheduleResin) -> None:
        await self.db.execute('INSERT OR REPLACE INTO schedule_resin VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
            [user.id, user.channel_id, datetime.now().isoformat(),
             user.threshold_resin, user.threshold_currency, user.threshold_transformer, user.threshold_expedition,
             user.check_commission_time.isoformat() if user.check_commission_time else None])
        await self.db.commit()
    
    async def remove(self, user_id: int) -> None:
        await self.db.execute('DELETE FROM schedule_resin WHERE id=?', [user_id])
        await self.db.commit()
    
    async def update(self, user_id: int, *, next_check_time: Optional[datetime] = None, check_commission_time: Optional[datetime] = None) -> None:
        if next_check_time:
            await self.db.execute(
                'UPDATE schedule_resin SET next_check_time=? WHERE id=?',
                [next_check_time.isoformat(), user_id])
        if check_commission_time:
            await self.db.execute(
                'UPDATE schedule_resin SET check_commission_time=? WHERE id=?',
                [check_commission_time.isoformat(), user_id]
            )
        await self.db.commit()

    async def get(self, user_id: int) -> Optional[ScheduleResin]:
        async with self.db.execute('SELECT * FROM schedule_resin WHERE id=?', [user_id]) as cursor:
            row = await cursor.fetchone()
            return ScheduleResin.fromRow(row) if row else None

    async def getAll(self) -> List[ScheduleResin]:
        async with self.db.execute('SELECT * FROM schedule_resin') as cursor:
            rows = await cursor.fetchall()
            return [ScheduleResin.fromRow(row) for row in rows]
