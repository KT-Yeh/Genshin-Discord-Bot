import asyncio
import shutil
from datetime import date, datetime

import sentry_sdk
from discord.ext import commands, tasks

import database
from genshin_py import auto_task
from utility import config
from utility.custom_log import LOG


class ScheduleLoopCog(commands.Cog, name="排程循環"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.schedule.start()

    async def cog_unload(self) -> None:
        self.schedule.cancel()

    loop_interval = 1  # 循環間隔1分鐘

    @tasks.loop(minutes=loop_interval)
    async def schedule(self):
        """排程主循環，每 {loop_interval} 分鐘執行排程相關函式"""

        now = datetime.now()
        # 確認沒有在遊戲維護時間內
        if config.game_maintenance_time is None or not (
            config.game_maintenance_time[0] <= now < config.game_maintenance_time[1]
        ):
            # 每 {config.schedule_daily_checkin_interval} 分鐘啟動自動簽到
            if now.minute % config.schedule_daily_checkin_interval < self.loop_interval:
                asyncio.create_task(auto_task.DailyReward.execute(self.bot))

            # 每 {config.schedule_check_resin_interval} 分鐘檢查一次樹脂
            if now.minute % config.schedule_check_resin_interval < self.loop_interval:
                asyncio.create_task(auto_task.RealtimeNotes.execute(self.bot))

        # 每日凌晨一點備份資料庫、刪除過期使用者資料
        if now.hour == 1 and now.minute < self.loop_interval:
            try:
                db_path = "data/bot/bot.db"
                today = date.today()
                shutil.copyfile(db_path, f"{db_path.split('.')[0]}_backup_{today}.db")
            except Exception as e:
                LOG.Error(str(e))
                sentry_sdk.capture_exception(e)
            asyncio.create_task(database.Tool.remove_expired_user(config.expired_user_days))

    @schedule.before_loop
    async def before_schedule(self):
        await self.bot.wait_until_ready()


async def setup(client: commands.Bot):
    await client.add_cog(ScheduleLoopCog(client))
