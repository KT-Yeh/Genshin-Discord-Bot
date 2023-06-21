from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

import aiosqlite


@dataclass
class ScheduleDaily:
    """每日簽到 Table 的資料類別

    Attributes
    -----
    id: `int`
        使用者 Discord ID
    channel_id: `int`
        發送通知訊息的 Discord 頻道的 ID
    is_mention: `bool`
        發送訊息時是否要 tag 使用者
    has_genshin: `bool`
        是否要簽到原神
    has_honkai: `bool`
        是否要簽到崩壞3
    has_starrail: `bool`
        是否要簽到星穹鐵道
    last_checkin_date: `Optional[date]`
        用來記錄上次簽到的日期，在特殊情況下避免重複簽到
    """

    id: int
    channel_id: int
    is_mention: bool = False
    has_genshin: bool = False
    has_honkai: bool = False
    has_starrail: bool = False
    last_checkin_date: Optional[date] = None

    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> ScheduleDaily:
        return cls(
            id=row["id"],
            channel_id=row["channel_id"],
            is_mention=bool(row["is_mention"]),
            has_genshin=bool(row["has_genshin"]),
            has_honkai=bool(row["has_honkai"]),
            has_starrail=bool(row["has_starrail"]),
            last_checkin_date=(
                None
                if row["last_checkin_date"] is None
                else date.fromisoformat(row["last_checkin_date"])
            ),
        )


class ScheduleDailyTable:
    """每日簽到資料的 Table"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        """在資料庫新建 Table"""
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS schedule_daily (
                id int NOT NULL PRIMARY KEY,
                channel_id int NOT NULL,
                is_mention int NOT NULL,
                has_genshin int NOT NULL,
                has_honkai int NOT NULL,
                has_starrail int NOT NULL,
                last_checkin_date text
            )"""
        )
        cursor = await self.db.execute("PRAGMA table_info(schedule_daily)")
        columns = [column[1] for column in await cursor.fetchall()]

        if "has_genshin" not in columns:
            await self.db.execute(
                "ALTER TABLE schedule_daily ADD COLUMN has_genshin int NOT NULL DEFAULT '1'"
            )
        if "has_starrail" not in columns:
            await self.db.execute(
                "ALTER TABLE schedule_daily ADD COLUMN has_starrail int NOT NULL DEFAULT '0'"
            )
        await self.db.commit()

    async def add(self, user: ScheduleDaily) -> None:
        """新增使用者到 Table"""
        if (await self.get(user.id)) is not None:  # 當使用者已存在時
            await self.db.execute(
                "UPDATE schedule_daily SET "
                "channel_id=?, is_mention=?, has_genshin=?, has_honkai=?, has_starrail=? WHERE id=?",
                [
                    user.channel_id,
                    int(user.is_mention),
                    int(user.has_genshin),
                    int(user.has_honkai),
                    int(user.has_starrail),
                    user.id,
                ],
            )
        else:
            await self.db.execute(
                "INSERT OR REPLACE INTO schedule_daily"
                "(id, channel_id, is_mention, has_genshin, has_honkai, has_starrail, last_checkin_date) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                [
                    user.id,
                    user.channel_id,
                    int(user.is_mention),
                    int(user.has_genshin),
                    int(user.has_honkai),
                    int(user.has_starrail),
                    user.last_checkin_date,
                ],
            )
        await self.db.commit()

    async def remove(self, user_id: int) -> None:
        """從 Table 移除指定的使用者"""
        await self.db.execute("DELETE FROM schedule_daily WHERE id=?", [user_id])
        await self.db.commit()

    async def update(self, user_id: int, *, last_checkin_date: bool = False) -> None:
        """更新指定使用者的 Column 資料"""
        if last_checkin_date:
            await self.db.execute(
                "UPDATE schedule_daily SET last_checkin_date=? WHERE id=?",
                [date.today().isoformat(), user_id],
            )
        await self.db.commit()

    async def get(self, user_id: int) -> Optional[ScheduleDaily]:
        """取得指定使用者的資料"""
        async with self.db.execute("SELECT * FROM schedule_daily WHERE id=?", [user_id]) as cursor:
            row = await cursor.fetchone()
            return ScheduleDaily.fromRow(row) if row else None

    async def getAll(self) -> List[ScheduleDaily]:
        """取得所有使用者的資料"""
        async with self.db.execute("SELECT * FROM schedule_daily") as cursor:
            rows = await cursor.fetchall()
            return [ScheduleDaily.fromRow(row) for row in rows]

    async def getTotalNumber(self) -> int:
        """取得 Table 內的資料總筆數"""
        async with self.db.execute("SELECT COUNT(id) FROM schedule_daily") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
