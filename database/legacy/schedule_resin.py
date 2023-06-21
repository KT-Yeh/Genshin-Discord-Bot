from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import aiosqlite


@dataclass
class ScheduleResin:
    """自動檢查即時便箋 Table 的資料類別

    Attributes
    -----
    id: `int`
        使用者 Discord ID
    channel_id: `int`
        發送通知訊息的 Discord 頻道的 ID
    next_check_time: `Optional[datetime]`
        下次檢查的時間，當檢查時超過此時間才會對 Hoyolab 請求資料
    threshold_resin: `Optional[int]`
        樹脂額滿之前幾小時發送提醒
    threshold_currency: `Optional[int]`
        寶錢額滿之前幾小時發送提醒
    threshold_transformer: `Optional[int]`
        質變儀完成之前幾小時發送提醒
    threshold_expedition: `Optional[int]`
        全部派遣完成之前幾小時發送提醒
    check_commission_time: `Optional[datetime]`
        每天幾點提醒今天的委託任務還未完成
    """

    id: int
    channel_id: int
    next_check_time: Optional[datetime] = None
    threshold_resin: Optional[int] = None
    threshold_currency: Optional[int] = None
    threshold_transformer: Optional[int] = None
    threshold_expedition: Optional[int] = None
    check_commission_time: Optional[datetime] = None

    @classmethod
    def fromRow(cls, row: aiosqlite.Row) -> ScheduleResin:
        return cls(
            id=row["id"],
            channel_id=row["channel_id"],
            next_check_time=(
                datetime.fromisoformat(row["next_check_time"]) if row["next_check_time"] else None
            ),
            threshold_resin=row["threshold_resin"],
            threshold_currency=row["threshold_currency"],
            threshold_transformer=row["threshold_transformer"],
            threshold_expedition=row["threshold_expedition"],
            check_commission_time=(
                datetime.fromisoformat(row["check_commission_time"])
                if row["check_commission_time"]
                else None
            ),
        )


class ScheduleResinTable:
    """檢查即時便箋資料的 Table"""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self) -> None:
        """在資料庫新建 Table"""
        await self.db.execute(
            """CREATE TABLE IF NOT EXISTS schedule_resin (
                id int NOT NULL PRIMARY KEY,
                channel_id int NOT NULL,
                next_check_time text,
                threshold_resin int,
                threshold_currency int,
                threshold_transformer int,
                threshold_expedition int,
                check_commission_time text
            )"""
        )
        await self.db.commit()

    async def add(self, user: ScheduleResin) -> None:
        """新增使用者到 Table"""
        await self.db.execute(
            "INSERT OR REPLACE INTO schedule_resin VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            [
                user.id,
                user.channel_id,
                datetime.now().isoformat(),
                user.threshold_resin,
                user.threshold_currency,
                user.threshold_transformer,
                user.threshold_expedition,
                user.check_commission_time.isoformat() if user.check_commission_time else None,
            ],
        )
        await self.db.commit()

    async def remove(self, user_id: int) -> None:
        """從 Table 移除指定的使用者"""
        await self.db.execute("DELETE FROM schedule_resin WHERE id=?", [user_id])
        await self.db.commit()

    async def update(
        self,
        user_id: int,
        *,
        next_check_time: Optional[datetime] = None,
        check_commission_time: Optional[datetime] = None,
    ) -> None:
        """更新指定使用者的 Column 資料"""
        if next_check_time:
            await self.db.execute(
                "UPDATE schedule_resin SET next_check_time=? WHERE id=?",
                [next_check_time.isoformat(), user_id],
            )
        if check_commission_time:
            await self.db.execute(
                "UPDATE schedule_resin SET check_commission_time=? WHERE id=?",
                [check_commission_time.isoformat(), user_id],
            )
        await self.db.commit()

    async def get(self, user_id: int) -> Optional[ScheduleResin]:
        """取得指定使用者的資料"""
        async with self.db.execute("SELECT * FROM schedule_resin WHERE id=?", [user_id]) as cursor:
            row = await cursor.fetchone()
            return ScheduleResin.fromRow(row) if row else None

    async def getAll(self) -> List[ScheduleResin]:
        """取得所有使用者的資料"""
        async with self.db.execute("SELECT * FROM schedule_resin") as cursor:
            rows = await cursor.fetchall()
            return [ScheduleResin.fromRow(row) for row in rows]
