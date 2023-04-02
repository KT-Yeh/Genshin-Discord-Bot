import asyncio
from datetime import date, datetime
from typing import ClassVar

import discord
import sentry_sdk
from discord.ext import commands

from data.database import db
from utility import LOG, EmbedTemplate, config

from .. import genshin_app


class DailyReward:
    """自動排程的類別

    Methods
    -----
    execute(bot: `commands.Bot`)
        執行自動排程
    """

    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    @classmethod
    async def execute(cls, bot: commands.Bot):
        """執行自動排程

        Parameters
        -----
        bot: `commands.Bot`
            Discord 機器人客戶端
        """
        if cls._lock.locked():
            return
        await cls._lock.acquire()
        try:
            await cls._claim_daily_reward(bot)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            LOG.Error(f"自動排程 DailyReward 發生錯誤：{e}")
        finally:
            cls._lock.release()

    @classmethod
    async def _claim_daily_reward(cls, bot: commands.Bot) -> float:
        """替資料庫內有登記自動每日簽到的使用者簽到

        Parameters
        -----
        bot: `discord.Client`
            Discord 機器人客戶端

        Returns
        -----
        `float`
            每位使用者平均簽到時間
        """

        LOG.System("每日自動簽到開始")
        start_time = datetime.now()  # 簽到開始時間
        total, honkai_count = 0, 0  # 統計簽到人數
        daily_users = await db.schedule_daily.getAll()
        for user in daily_users:
            # 檢查今天是否已經簽到過
            if user.last_checkin_date == date.today():
                continue
            # 簽到並更新最後簽到時間
            result = await genshin_app.claim_daily_reward(
                user.id, honkai=user.has_honkai, schedule=True
            )
            await db.schedule_daily.update(user.id, last_checkin_date=True)
            total += 1
            honkai_count += int(user.has_honkai)
            try:
                channel = bot.get_channel(user.channel_id) or await bot.fetch_channel(
                    user.channel_id
                )
                # 若不用@提及使用者，則先取得此使用者的暱稱然後發送訊息
                if user.is_mention is False:
                    _user = await bot.fetch_user(user.id)
                    await channel.send(f"[自動簽到] {_user.display_name}：{result}")  # type: ignore
                else:
                    await channel.send(f"[自動簽到] <@{user.id}> {result}")  # type: ignore
            except (
                discord.Forbidden,
                discord.NotFound,
                discord.InvalidData,
            ) as e:  # 發送訊息失敗，移除此使用者
                LOG.Except(f"自動簽到發送訊息失敗，移除此使用者 {LOG.User(user.id)}：{e}")
                await db.schedule_daily.remove(user.id)
            except Exception as e:
                sentry_sdk.capture_exception(e)
            await asyncio.sleep(config.schedule_loop_delay)
        LOG.System(f"每日自動簽到結束，總共 {total} 人簽到，其中 {honkai_count} 人也簽到崩壞3")
        # 計算平均簽到時間
        end_time = datetime.now()
        avg_user_daily_time = (end_time - start_time).total_seconds() / (total if total > 0 else 1)

        # 將平均簽到時間儲存到 schedule cog
        schedule_cog = bot.get_cog("自動化")
        if schedule_cog is not None:
            setattr(schedule_cog, "avg_user_daily_time", avg_user_daily_time)

        # 發送統計結果到通知頻道
        if config.notification_channel_id:
            embed = EmbedTemplate.normal(
                f"總共 {total} 人簽到，其中 {honkai_count} 人也簽到崩壞3\n"
                f"簽到時間：{start_time.strftime('%H:%M:%S')} ~ {end_time.strftime('%H:%M:%S')}\n"
                f"平均時間：{avg_user_daily_time:.2f} 秒/人",
                title="每日自動簽到結果",
            )
            _id = config.notification_channel_id
            _channel = bot.get_channel(_id) or await bot.fetch_channel(_id)
            if isinstance(_channel, (discord.TextChannel, discord.Thread, discord.DMChannel)):
                await _channel.send(embed=embed)

        return avg_user_daily_time
