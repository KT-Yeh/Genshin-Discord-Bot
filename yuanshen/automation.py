"""此模組的函式用來給 schedule cog 使用，包含了自動排程執行時會用到的每日簽到與確認即時便箋"""

import asyncio
import discord
import genshin
from discord.ext import commands
from datetime import datetime, date, timedelta
from typing import Callable
from . import genshin_app, parser, GenshinAPIException
from cogs.schedule import Schedule
from utility import config, EmbedTemplate, LOG
from data.database import db


async def claim_daily_reward(bot: commands.Bot) -> float:
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
            channel = bot.get_channel(user.channel_id) or await bot.fetch_channel(user.channel_id)
            # 若不用@提及使用者，則先取得此使用者的暱稱然後發送訊息
            if user.is_mention is False:
                _user = await bot.fetch_user(user.id)
                await channel.send(f"[自動簽到] {_user.display_name}：{result}")  # type: ignore
            else:
                await channel.send(f"[自動簽到] <@{user.id}> {result}")  # type: ignore
        except Exception as e:  # 發送訊息失敗，移除此使用者
            LOG.Except(f"自動簽到發送訊息失敗，移除此使用者 {LOG.User(user.id)}：{e}")
            await db.schedule_daily.remove(user.id)
        await asyncio.sleep(config.schedule_loop_delay)
    LOG.System(f"每日自動簽到結束，總共 {total} 人簽到，其中 {honkai_count} 人也簽到崩壞3")
    # 計算平均簽到時間
    end_time = datetime.now()
    avg_user_daily_time = (end_time - start_time).total_seconds() / (total if total > 0 else 1)

    # 將平均簽到時間儲存到 schedule cog
    schedule_cog = bot.get_cog("自動化")
    if isinstance(schedule_cog, Schedule):
        schedule_cog.avg_user_daily_time = avg_user_daily_time

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


async def check_realtime_notes(bot: commands.Bot):
    """檢查使用者的即時便箋狀態，依據每位使用者的設定檢查，並在超出設定值時發出提醒

    Parameters
    -----
    bot: `discord.Client`
        Discord 機器人客戶端
    """
    LOG.System("自動檢查樹脂開始")
    resin_users = await db.schedule_resin.getAll()
    count = 0  # 統計人數
    for _u in resin_users:
        # 要檢查的當下從資料庫重新取得最新的使用者資料
        if (user := await db.schedule_resin.get(_u.id)) is None:
            continue
        # 若還沒到檢查時間則跳過此使用者
        if user.next_check_time and datetime.now() < user.next_check_time:
            continue
        # 檢查使用者即時便箋
        msg = ""
        embed = discord.Embed()
        try:
            notes = await genshin_app.get_realtime_notes(user.id, schedule=True)
        except Exception as e:
            # 當錯誤為 InternalDatabaseError 時，忽略並設定1小時後檢查
            if isinstance(e, GenshinAPIException) and isinstance(
                e.origin, genshin.errors.InternalDatabaseError
            ):
                await db.schedule_resin.update(
                    user.id, next_check_time=(datetime.now() + timedelta(hours=1))
                )
            else:
                msg = f"自動檢查樹脂時發生錯誤：{str(e)}\n預計5小時後再檢查"
                # 當發生錯誤時，預計5小時後再檢查
                await db.schedule_resin.update(
                    user.id, next_check_time=(datetime.now() + timedelta(hours=5))
                )
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
        count += 1
        # 當有錯誤訊息或是樹脂快要溢出時，向使用者發送訊息
        if len(msg) > 0:
            try:  # 發送訊息提醒使用者
                channel = bot.get_channel(user.channel_id) or await bot.fetch_channel(
                    user.channel_id
                )
                _user = await bot.fetch_user(user.id)
                msg_sent = await channel.send(f"{_user.mention}，{msg}", embed=embed)  # type: ignore
            except Exception as e:  # 發送訊息失敗，移除此使用者
                LOG.Except(f"自動檢查樹脂發送訊息失敗，移除此使用者 {LOG.User(user.id)}：{e}")
                await db.schedule_resin.remove(user.id)
            else:  # 成功發送訊息
                # 若使用者不在發送訊息的頻道則移除
                if _user.mentioned_in(msg_sent) is False:
                    LOG.Except(f"自動檢查樹脂使用者不在頻道，移除此使用者 {LOG.User(_user)}")
                    await db.schedule_resin.remove(user.id)
        await asyncio.sleep(config.schedule_loop_delay)
    LOG.System(f"自動檢查樹脂結束，{count}/{len(resin_users)} 人已檢查")
