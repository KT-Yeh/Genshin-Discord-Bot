import typing
import aiosqlite
from datetime import date

class ScheduleDaily:
    id: int
    channel_id: int
    is_mention: bool
    has_honkai: bool
    last_checkin_date: date

    def __init__(self, *, id: int = None, channel_id: int = None, is_mention: bool = None, has_honkai: bool = None, last_checkin_date: date = None):
        self.id = id
        self.channel_id = channel_id
        self.is_mention = is_mention
        self.has_honkai = has_honkai
        self.last_checkin_date = last_checkin_date
    
    @classmethod
    def fromRow(cls, row: aiosqlite.Row):
        try:
            return cls(
                id=row['id'],
                channel_id=row['channel_id'],
                is_mention=bool(row['is_mention']),
                has_honkai=bool(row['has_honkai']),
                last_checkin_date=(None if row['last_checkin_date'] == None else date.fromisoformat(row['last_checkin_date']))
            )
        except:
            return cls()

class ScheduleDailyTable:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        await self.db.execute('''CREATE TABLE IF NOT EXISTS schedule_daily (
                id int NOT NULL UNIQUE,
                channel_id int,
                is_mention int,
                has_honkai int,
                last_checkin_date text
            )''')
        await self.db.commit()

    async def add(self, user: ScheduleDaily) -> None:
        await self.db.execute('INSERT OR REPLACE INTO schedule_daily VALUES(?, ?, ?, ?, ?)',
            [user.id, user.channel_id, int(user.is_mention), int(user.has_honkai), None])
        await self.db.commit()
    
    async def remove(self, user_id: int) -> None:
        await self.db.execute('DELETE FROM schedule_daily WHERE id=?', [user_id])
        await self.db.commit()
    
    async def update(self, user_id: int, *, last_checkin_date: bool = False) -> None:
        if last_checkin_date:
            await self.db.execute('UPDATE schedule_daily SET last_checkin_date=? WHERE id=?',
                [date.today().isoformat(), user_id])
        await self.db.commit()

    async def get(self, user_id: int) -> ScheduleDaily:
        async with self.db.execute('SELECT * FROM schedule_daily WHERE id=?', [user_id]) as cursor:
            row = await cursor.fetchone()
            return ScheduleDaily.fromRow(row)

    async def getAll(self) -> typing.List[ScheduleDaily]:
        async with self.db.execute('SELECT * FROM schedule_daily') as cursor:
            rows = await cursor.fetchall()
            return [ScheduleDaily.fromRow(row) for row in rows]
