import asyncio
from datetime import datetime
from typing import Awaitable, Callable, ClassVar

import discord
import sentry_sdk
import sqlalchemy
from discord.ext import commands

from database import Database, GenshinScheduleNotes, StarrailScheduleNotes, ZZZScheduleNotes
from utility import LOG, config

from .common import CheckResult, T_User
from .genshin import check_genshin_notes
from .starrail import check_starrail_notes
from .zzz import check_zzz_notes


class RealtimeNotes:
    """自動排程的類別

    Methods
    -----
    execute(bot: `commands.Bot`)
        執行自動排程
    """

    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _bot: commands.Bot

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
        cls._bot = bot
        try:
            LOG.System("自動檢查樹脂開始")
            await asyncio.gather(
                cls._check_games_note(GenshinScheduleNotes, "原神", check_genshin_notes),
                cls._check_games_note(StarrailScheduleNotes, "星穹鐵道", check_starrail_notes),
                cls._check_games_note(ZZZScheduleNotes, "絕區零", check_zzz_notes),
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            LOG.Error(f"自動排程 RealtimeNotes 發生錯誤：{e}")
        finally:
            cls._lock.release()

    @classmethod
    async def _check_games_note(
        cls,
        game_orm: type[T_User],
        game_name: str,
        game_check_fucntion: Callable[[T_User], Awaitable[CheckResult | None]],
    ) -> None:
        """檢查指定遊戲的所有使用者的即時便箋

        Parameters
        ----------
        game_orm: Type[`T_User`]
            排程檢查即時便箋的 ORM（物件關聯對映）類型
        game_name: `str`
            遊戲名稱
        game_check_function: Callable[[`T_User`], Awaitable[`CheckResult` | `None`]]
            檢查遊戲便箋的函式

        """
        count = 0
        # 選擇所有使用者 ID
        stmt = sqlalchemy.select(game_orm.discord_id)
        async with Database.sessionmaker() as session:
            user_ids = (await session.execute(stmt)).scalars().all()
        for user_id in user_ids:
            # 取得要檢查的使用者，若檢查時間還沒到則跳過
            user = await Database.select_one(game_orm, game_orm.discord_id.is_(user_id))
            if user is None or user.next_check_time and datetime.now() < user.next_check_time:
                continue
            r = await game_check_fucntion(user)
            if r is not None:
                count += 1
            # 當有錯誤訊息或是即時便箋快要額滿時，向使用者發送訊息
            if r and len(r.message) > 0:
                await cls._send_message(user, r.message, r.embed)
            # 使用者之間的檢查間隔時間
            await asyncio.sleep(config.schedule_loop_delay)
        LOG.System(f"{game_name}自動檢查即時便箋結束，{count}/{len(user_ids)} 人已檢查")

    @classmethod
    async def _send_message(cls, user: T_User, message: str, embed: discord.Embed) -> None:
        """發送訊息提醒使用者"""
        bot = cls._bot
        try:
            _id = user.discord_channel_id
            channel = bot.get_channel(_id) or await bot.fetch_channel(_id)
            discord_user = bot.get_user(user.discord_id) or await bot.fetch_user(user.discord_id)
            msg_sent = await channel.send(f"{discord_user.mention}，{message}", embed=embed)  # type: ignore
        except (
            discord.Forbidden,
            discord.NotFound,
            discord.InvalidData,
        ) as e:  # 發送訊息失敗，移除此使用者
            LOG.Except(
                f"自動檢查即時便箋發送訊息失敗，移除此使用者 {LOG.User(user.discord_id)}：{e}"
            )
            await Database.delete_instance(user)
        except Exception as e:
            sentry_sdk.capture_exception(e)
        else:  # 成功發送訊息
            # 若使用者不在發送訊息的頻道則移除
            if discord_user.mentioned_in(msg_sent) is False:
                LOG.Except(
                    f"自動檢查即時便箋使用者不在頻道，移除此使用者 {LOG.User(discord_user)}"
                )
                await Database.delete_instance(user)
