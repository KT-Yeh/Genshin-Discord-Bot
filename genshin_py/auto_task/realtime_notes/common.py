from datetime import datetime, timedelta
from typing import NamedTuple, TypeVar

import discord
import genshin

from database import Database, GenshinScheduleNotes, StarrailScheduleNotes

from ... import errors, get_genshin_notes, get_starrail_notes

T_User = TypeVar("T_User", GenshinScheduleNotes, StarrailScheduleNotes)


class CheckResult(NamedTuple):
    """`tuple[str, embed]`: The return result of the check_xxx_notes function"""

    message: str
    embed: discord.Embed


async def get_realtime_notes(
    user: T_User,
) -> genshin.models.Notes | genshin.models.StarRailNote | None:
    """根據傳入的使用者取得即時便箋，若發生 InternalDatabaseError 以外的例外則拋出"""
    notes = None
    try:
        if isinstance(user, GenshinScheduleNotes):
            notes = await get_genshin_notes(user.discord_id)
        if isinstance(user, StarrailScheduleNotes):
            notes = await get_starrail_notes(user.discord_id)
    except Exception as e:
        # 當錯誤為 InternalDatabaseError 時，忽略並設定1小時後檢查
        if isinstance(e, errors.GenshinAPIException) and isinstance(
            e.origin, genshin.errors.InternalDatabaseError
        ):
            user.next_check_time = datetime.now() + timedelta(hours=1)
            await Database.insert_or_replace(user)
        else:  # 當發生錯誤時，預計5小時後再檢查
            user.next_check_time = datetime.now() + timedelta(hours=5)
            await Database.insert_or_replace(user)
            raise e
    return notes


def cal_next_check_time(remaining: timedelta, user_threshold: int) -> datetime:
    """計算下次檢查時間的函式

    Parameters
    ------
    remaining: `timedelta`:
        剩餘時間
    user_threshold: `int`
        使用者設定的提醒閾值，以小時為單位。

    Returns
    ------
    `datetime`:
        下次檢查的時間點。
    """
    remaining_hours: float = remaining.total_seconds() / 3600
    if remaining_hours > user_threshold:
        # 當剩餘時間比使用者設定的提醒時間還久，則回傳使用者設定的時間點
        return datetime.now() + remaining - timedelta(hours=user_threshold)
    else:  # remaining <= user_threshold
        # 當剩餘時間較短時，我們取 3 次間隔作為提醒時間
        # 例如使用者設定 24 小時前提醒，則下次提醒的時間點為 16、8、0 小時前
        interval: float = user_threshold / 3
        user_threshold_f: float = float(user_threshold)
        while remaining_hours <= user_threshold_f:
            user_threshold_f -= interval
        return datetime.now() + remaining - timedelta(hours=user_threshold_f)
