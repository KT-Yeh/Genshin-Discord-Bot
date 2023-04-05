import asyncio
from datetime import datetime, timedelta
from typing import Callable, ClassVar

import discord
import genshin
import sentry_sdk
from discord.ext import commands

from data.database import ScheduleResin, db
from utility import LOG, EmbedTemplate, config

from .. import errors, genshin_app, parser


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
            resin_users = await db.schedule_resin.getAll()

            for user in resin_users:
                result = await cls._check_realtime_notes(user.id)
                if result is None:
                    continue
                count += 1
                msg, embed = result
                # 當有錯誤訊息或是樹脂快要溢出時，向使用者發送訊息
                if len(msg) > 0:
                    await cls._send_message(bot, user, msg, embed)
                # 使用者之間的檢查間隔時間
                await asyncio.sleep(config.schedule_loop_delay)

            LOG.System(f"自動檢查樹脂結束，{count}/{len(resin_users)} 人已檢查")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            LOG.Error(f"自動排程 RealtimeNotes 發生錯誤：{e}")
        finally:
            cls._lock.release()

    @classmethod
    async def _check_realtime_notes(cls, user_discord_id: int) -> tuple[str, discord.Embed] | None:
        """檢查使用者的即時便箋狀態，依據每位使用者的設定檢查，並在超出設定值時發出提醒

        Parameters
        -----
        user_discord_id: `int`
            使用者的 Discord ID

        Returns
        -----
        `tuple[str, discord.Embed] | None`
            - 若有錯誤訊息或是樹脂快要溢出時，回傳訊息與 Embed 物件
            - 若跳過此使用者，回傳 None
        """
        # 要檢查的當下從資料庫重新取得最新的使用者資料
        if (user := await db.schedule_resin.get(user_discord_id)) is None:
            return None
        # 若還沒到檢查時間則跳過此使用者
        if user.next_check_time and datetime.now() < user.next_check_time:
            return None
        # 檢查使用者即時便箋
        msg = ""
        embed = None
        try:
            notes = await genshin_app.get_realtime_notes(user.id, schedule=True)
        except Exception as e:
            # 當錯誤為 InternalDatabaseError 時，忽略並設定1小時後檢查
            if isinstance(e, errors.GenshinAPIException) and isinstance(
                e.origin, genshin.errors.InternalDatabaseError
            ):
                await db.schedule_resin.update(
                    user.id, next_check_time=(datetime.now() + timedelta(hours=1))
                )
            else:
                msg = "自動檢查樹脂時發生錯誤，預計5小時後再檢查"
                embed = EmbedTemplate.error(e)
                # 當發生錯誤時，預計5小時後再檢查
                await db.schedule_resin.update(
                    user.id, next_check_time=(datetime.now() + timedelta(hours=5))
                )
                return (msg, embed)
        else:  # 正常檢查即時便箋
            embed = await parser.parse_realtime_notes(notes, shortForm=True)
            next_check_time: list[datetime] = [datetime.now() + timedelta(days=1)]  # 設定一個基本的下次檢查時間
            # 計算下次檢查時間的函式：預計完成時間-使用者設定的時間
            cal_nxt_check_time: Callable[[timedelta, int], datetime] = (
                lambda remaining, user_threshold: datetime.now()
                + remaining
                - timedelta(hours=user_threshold)
            )
            # 檢查樹脂
            if isinstance(user.threshold_resin, int):
                # 當樹脂距離額滿時間低於設定值，則設定要發送的訊息
                if notes.remaining_resin_recovery_time <= timedelta(
                    hours=user.threshold_resin, seconds=10
                ):
                    msg += (
                        "樹脂已經額滿啦！"
                        if notes.remaining_resin_recovery_time <= timedelta(0)
                        else "樹脂快要額滿啦！"
                    )
                # 設定下次檢查時間，當樹脂完全額滿時，預計6小時後再檢查；否則依照(預計完成-使用者設定的時間)
                next_check_time.append(
                    datetime.now() + timedelta(hours=6)
                    if notes.current_resin >= notes.max_resin
                    else cal_nxt_check_time(
                        notes.remaining_resin_recovery_time, user.threshold_resin
                    )
                )
            # 檢查洞天寶錢
            if isinstance(user.threshold_currency, int):
                if notes.remaining_realm_currency_recovery_time <= timedelta(
                    hours=user.threshold_currency, seconds=10
                ):
                    msg += (
                        "洞天寶錢已經額滿啦！"
                        if notes.remaining_realm_currency_recovery_time <= timedelta(0)
                        else "洞天寶錢快要額滿啦！"
                    )
                next_check_time.append(
                    datetime.now() + timedelta(hours=6)
                    if notes.current_realm_currency >= notes.max_realm_currency
                    else cal_nxt_check_time(
                        notes.remaining_realm_currency_recovery_time,
                        user.threshold_currency,
                    )
                )
            # 檢查質變儀
            if (
                isinstance(user.threshold_transformer, int)
                and notes.remaining_transformer_recovery_time is not None
            ):
                if notes.remaining_transformer_recovery_time <= timedelta(
                    hours=user.threshold_transformer, seconds=10
                ):
                    msg += (
                        "質變儀已經完成了！"
                        if notes.remaining_transformer_recovery_time <= timedelta(0)
                        else "質變儀快要完成了！"
                    )
                next_check_time.append(
                    datetime.now() + timedelta(hours=6)
                    if notes.remaining_transformer_recovery_time.total_seconds() <= 5
                    else cal_nxt_check_time(
                        notes.remaining_transformer_recovery_time,
                        user.threshold_transformer,
                    )
                )
            # 檢查探索派遣
            if isinstance(user.threshold_expedition, int) and len(notes.expeditions) > 0:
                # 選出剩餘時間最多的派遣
                longest_expedition = max(notes.expeditions, key=lambda epd: epd.remaining_time)
                if longest_expedition.remaining_time <= timedelta(
                    hours=user.threshold_expedition, seconds=10
                ):
                    msg += (
                        "探索派遣已經完成了！"
                        if longest_expedition.remaining_time <= timedelta(0)
                        else "探索派遣快要完成了！"
                    )
                next_check_time.append(
                    datetime.now() + timedelta(hours=6)
                    if longest_expedition.finished is True
                    else cal_nxt_check_time(
                        longest_expedition.remaining_time, user.threshold_expedition
                    )
                )
            # 檢查每日委託
            if isinstance(user.check_commission_time, datetime):
                _next_check_time = user.check_commission_time
                # 當現在時間已超過設定的檢查時間
                if datetime.now() >= user.check_commission_time:
                    if not notes.claimed_commission_reward:
                        msg += "今日的委託任務還未完成！"
                    # 下次檢查時間為今天+1天，並更新至資料庫
                    _next_check_time += timedelta(days=1)
                    await db.schedule_resin.update(user.id, check_commission_time=_next_check_time)
                next_check_time.append(_next_check_time)

            # 設定下次檢查時間，從上面設定的時間中取最小的值
            check_time = min(next_check_time)
            # 若此次需要發送訊息，則將下次檢查時間設為至少1小時
            if len(msg) > 0:
                check_time = max(check_time, datetime.now() + timedelta(minutes=60))
            await db.schedule_resin.update(user.id, next_check_time=check_time)

            return (msg, embed)
        return None

    @classmethod
    async def _send_message(
        cls, bot: commands.Bot, user: ScheduleResin, msg: str, embed: discord.Embed
    ) -> None:
        """發送訊息提醒使用者"""

        try:  # 發送訊息提醒使用者
            channel = bot.get_channel(user.channel_id) or await bot.fetch_channel(user.channel_id)
            _user = await bot.fetch_user(user.id)
            msg_sent = await channel.send(f"{_user.mention}，{msg}", embed=embed)  # type: ignore
        except (
            discord.Forbidden,
            discord.NotFound,
            discord.InvalidData,
        ) as e:  # 發送訊息失敗，移除此使用者
            LOG.Except(f"自動檢查樹脂發送訊息失敗，移除此使用者 {LOG.User(user.id)}：{e}")
            await db.schedule_resin.remove(user.id)
        except Exception as e:
            sentry_sdk.capture_exception(e)
        else:  # 成功發送訊息
            # 若使用者不在發送訊息的頻道則移除
            if _user.mentioned_in(msg_sent) is False:
                LOG.Except(f"自動檢查樹脂使用者不在頻道，移除此使用者 {LOG.User(_user)}")
                await db.schedule_resin.remove(user.id)
