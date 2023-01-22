from datetime import datetime

import aiosqlite

from utility.custom_log import LOG

from .schedule_daily import ScheduleDailyTable
from .schedule_resin import ScheduleResinTable
from .showcase import ShowcaseTable
from .spiral_abyss import SpiralAbyssTable
from .users import UsersTable


class Database:
    """資料庫主類別，用來管理所有資料庫內的 Table

    Attributes
    -----
    db: `aiosqlite.Connection`
        資料庫的連線，可以使用此變數直接操作資料庫
    users: `UsersTable`
        使用者資料的 Table
    schedule_daily: `ScheduleDailyTable`
        每日簽到的 Table
    schedule_resin: `ScheduleResinTable`
        即時便箋自動檢查的 Table
    spiral_abyss: `SpiralAbyssTable`
        深境螺旋資料的 Table
    showcase: `ShowcaseTable`
        展示櫃資料的 Table
    """

    db: aiosqlite.Connection

    async def create(self, filepath: str) -> None:
        """初始化資料庫，在 bot 最初運行時需要呼叫一次"""
        self.db = await aiosqlite.connect(filepath)
        self.db.row_factory = aiosqlite.Row

        self.users = UsersTable(self.db)
        self.schedule_daily = ScheduleDailyTable(self.db)
        self.schedule_resin = ScheduleResinTable(self.db)
        self.spiral_abyss = SpiralAbyssTable(self.db)
        self.showcase = ShowcaseTable(self.db)

        await self.users.create()
        await self.schedule_daily.create()
        await self.schedule_resin.create()
        await self.spiral_abyss.create()
        await self.showcase.create()

    async def close(self) -> None:
        """關閉資料庫，在 bot 關閉前需要呼叫一次"""
        await self.db.close()

    async def removeUser(self, user_id: int) -> None:
        """移除特定使用者所有資料"""
        await self.users.remove(user_id)
        await self.schedule_daily.remove(user_id)
        await self.schedule_resin.remove(user_id)
        await self.spiral_abyss.remove(user_id)

    async def removeExpiredUser(self, diff_days: int = 30) -> None:
        """將超過天數未使用的使用者刪除"""
        now = datetime.now()
        count = 0
        users = await self.users.getAll()
        for user in users:
            if user.last_used_time is None:
                continue
            interval = now - user.last_used_time
            if interval.days > diff_days:
                await self.removeUser(user.id)
                count += 1
        LOG.System(f"檢查過期使用者：{len(users)} 位使用者已檢查，已刪除 {count} 位過期使用者")


db = Database()
