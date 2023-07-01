import asyncio
from typing import ClassVar

import discord
import sentry_sdk
import sqlalchemy
from discord.ext import commands

from database import Database
from database import GenshinScheduleNotes as GSSN
from database import StarrailScheduleNotes as SRSN
from utility import LOG, config

from .common import CheckResult, T_User
from .genshin import check_genshin_notes
from .starrail import check_starrail_notes


class RealtimeNotes:
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
            LOG.System("自動檢查樹脂開始")
            count = 0  # 統計人數

            gs_stmt = sqlalchemy.select(GSSN.discord_id)  # 選擇所有原神使用者 ID
            sr_stmt = sqlalchemy.select(SRSN.discord_id)  # 選擇所有鐵道使用者 ID
            async with Database.sessionmaker() as session:
                gs_user_ids = (await session.execute(gs_stmt)).scalars().all()
                sr_user_ids = (await session.execute(sr_stmt)).scalars().all()

            user_ids = set(list(gs_user_ids) + list(sr_user_ids))
            for user_id in user_ids:
                # 檢查每一位使用者
                genshin_user = await Database.select_one(GSSN, GSSN.discord_id.is_(user_id))
                starrail_user = await Database.select_one(SRSN, SRSN.discord_id.is_(user_id))
                results: list[CheckResult | None] = []
                if genshin_user is not None:
                    results.append(await check_genshin_notes(genshin_user.discord_id))
                if starrail_user is not None:
                    results.append(await check_starrail_notes(starrail_user.discord_id))

                # 當結果全部都是 None 表示跳過此使用者，不列入 count 計算
                if any(results) is False:
                    continue
                count += 1

                messages: list[str] = []
                embeds: list[discord.Embed] = []
                for result in results:
                    if result and len(result.message) > 0:
                        messages.append(result.message)
                        embeds.append(result.embed)

                # 當有錯誤訊息或是樹脂快要溢出時，向使用者發送訊息
                if len(messages) > 0:
                    if genshin_user:
                        await cls._send_message(bot, genshin_user, messages, embeds)
                    elif starrail_user:
                        await cls._send_message(bot, starrail_user, messages, embeds)
                # 使用者之間的檢查間隔時間
                await asyncio.sleep(config.schedule_loop_delay)

            LOG.System(f"自動檢查樹脂結束，{count}/{len(user_ids)} 人已檢查")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            LOG.Error(f"自動排程 RealtimeNotes 發生錯誤：{e}")
        finally:
            cls._lock.release()

    @classmethod
    async def _send_message(
        cls, bot: commands.Bot, user: T_User, messages: list[str], embeds: list[discord.Embed]
    ) -> None:
        """發送訊息提醒使用者"""
        msg = "".join(messages)

        try:  # 發送訊息提醒使用者
            _id = user.discord_channel_id
            channel = bot.get_channel(_id) or await bot.fetch_channel(_id)
            discord_user = await bot.fetch_user(user.discord_id)
            msg_sent = await channel.send(f"{discord_user.mention}，{msg}", embeds=embeds)  # type: ignore
        except (
            discord.Forbidden,
            discord.NotFound,
            discord.InvalidData,
        ) as e:  # 發送訊息失敗，移除此使用者
            LOG.Except(f"自動檢查樹脂發送訊息失敗，移除此使用者 {LOG.User(user.discord_id)}：{e}")
            await Database.delete_instance(user)
        except Exception as e:
            sentry_sdk.capture_exception(e)
        else:  # 成功發送訊息
            # 若使用者不在發送訊息的頻道則移除
            if discord_user.mentioned_in(msg_sent) is False:
                LOG.Except(f"自動檢查樹脂使用者不在頻道，移除此使用者 {LOG.User(discord_user)}")
                await Database.delete_instance(user)
