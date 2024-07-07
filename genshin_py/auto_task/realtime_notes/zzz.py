from datetime import datetime, timedelta

import genshin

from database import Database, ZZZScheduleNotes
from utility import EmbedTemplate

from ... import parse_zzz_notes
from .common import CheckResult, cal_next_check_time, get_realtime_notes


async def check_zzz_notes(user: ZZZScheduleNotes) -> CheckResult | None:
    """依據每位使用者的設定檢查即時便箋，若超出設定值時則回傳提醒訊息；若跳過此使用者，回傳 None"""
    try:
        notes = await get_realtime_notes(user)
    except Exception as e:
        return CheckResult(
            "絕區零自動檢查即時便箋時發生錯誤，預計5小時後再檢查。", EmbedTemplate.error(e)
        )

    if not isinstance(notes, genshin.models.ZZZNotes):
        return None

    msg = await check_threshold(user, notes)
    embed = await parse_zzz_notes(notes)
    return CheckResult(msg, embed)


async def check_threshold(user: ZZZScheduleNotes, notes: genshin.models.ZZZNotes) -> str:
    msg = ""
    # 設定一個基本的下次檢查時間
    next_check_time: list[datetime] = [datetime.now() + timedelta(days=1)]

    # 檢查電量
    if isinstance(user.threshold_battery, int):
        # 當電量距離額滿時間低於設定值，則設定要發送的訊息
        if timedelta(seconds=notes.battery_charge.seconds_till_full) <= timedelta(
            hours=user.threshold_battery
        ):
            msg += "電量已經充滿啦！" if notes.battery_charge.is_full else "電量快要充滿啦！"
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if notes.battery_charge.is_full
            else cal_next_check_time(
                timedelta(seconds=notes.battery_charge.seconds_till_full), user.threshold_battery
            )
        )
    # 檢查今日活躍度
    if isinstance(user.check_daily_engagement_time, datetime):
        # 當現在時間已超過設定的檢查時間
        if datetime.now() >= user.check_daily_engagement_time:
            if notes.engagement.current < notes.engagement.max:
                msg += "今日活躍度還未完成！"
            # 下次檢查時間為今天+1天，並更新至資料庫
            user.check_daily_engagement_time += timedelta(days=1)
        next_check_time.append(user.check_daily_engagement_time)

    # 設定下次檢查時間，從上面設定的時間中取最小的值
    check_time = min(next_check_time)
    # 若此次需要發送訊息，則將下次檢查時間設為至少1小時
    if len(msg) > 0:
        check_time = max(check_time, datetime.now() + timedelta(minutes=60))
    user.next_check_time = check_time
    await Database.insert_or_replace(user)

    return msg
