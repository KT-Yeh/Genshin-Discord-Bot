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


async def get_user(user_id: int, table: type[T_User]) -> T_User | None:
    """取得要檢查的使用者，若檢查時間還沒到則回傳 None"""
    user = await Database.select_one(table, table.discord_id.is_(user_id))
    if user is None:
        return None
    if user.next_check_time and datetime.now() < user.next_check_time:
        return None
    return user


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
    """計算下次檢查時間的函式：預計完成時間-使用者設定的時間"""
    return datetime.now() + remaining - timedelta(hours=user_threshold)
