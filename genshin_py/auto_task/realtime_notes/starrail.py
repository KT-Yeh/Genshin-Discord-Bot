from datetime import datetime, timedelta

import genshin

from database import Database, StarrailScheduleNotes
from utility import EmbedTemplate

from ... import parse_starrail_notes
from .common import CheckResult, cal_next_check_time, get_realtime_notes


async def check_starrail_notes(user: StarrailScheduleNotes) -> CheckResult | None:
    """依據每位使用者的設定檢查即時便箋，若超出設定值時則回傳提醒訊息；若跳過此使用者，回傳 None"""
    try:
        notes = await get_realtime_notes(user)
    except Exception as e:
        return CheckResult("星穹鐵道自動檢查即時便箋時發生錯誤，預計5小時後再檢查。", EmbedTemplate.error(e))

    if not isinstance(notes, genshin.models.StarRailNote):
        return None

    msg = await check_threshold(user, notes)
    embed = await parse_starrail_notes(notes, short_form=True)
    return CheckResult(msg, embed)


async def check_threshold(user: StarrailScheduleNotes, notes: genshin.models.StarRailNote) -> str:
    msg = ""
    # 設定一個基本的下次檢查時間
    next_check_time: list[datetime] = [datetime.now() + timedelta(days=1)]

    # 檢查開拓力
    if isinstance(user.threshold_power, int):
        # 當開拓力距離額滿時間低於設定值，則設定要發送的訊息
        if notes.stamina_recover_time <= timedelta(hours=user.threshold_power):
            msg += "開拓力已經額滿啦！" if notes.stamina_recover_time <= timedelta(0) else "開拓力快要額滿啦！"
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if notes.current_stamina >= notes.max_stamina
            else cal_next_check_time(notes.stamina_recover_time, user.threshold_power)
        )
    # 檢查委託
    if isinstance(user.threshold_expedition, int) and len(notes.expeditions) > 0:
        longest_expedition = max(notes.expeditions, key=lambda epd: epd.remaining_time)
        if longest_expedition.remaining_time <= timedelta(hours=user.threshold_expedition):
            msg += "委託已經完成了！" if longest_expedition.remaining_time <= timedelta(0) else "委託快要完成了！"
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if longest_expedition.finished is True
            else cal_next_check_time(longest_expedition.remaining_time, user.threshold_expedition)
        )
    # 檢查每日實訓
    if isinstance(user.check_daily_training_time, datetime):
        # 當現在時間已超過設定的檢查時間
        if datetime.now() >= user.check_daily_training_time:
            if notes.current_train_score < notes.max_train_score:
                msg += "今日的每日實訓還未完成！"
            # 下次檢查時間為今天+1天，並更新至資料庫
            user.check_daily_training_time += timedelta(days=1)
        next_check_time.append(user.check_daily_training_time)

    # 設定下次檢查時間，從上面設定的時間中取最小的值
    check_time = min(next_check_time)
    # 若此次需要發送訊息，則將下次檢查時間設為至少1小時
    if len(msg) > 0:
        check_time = max(check_time, datetime.now() + timedelta(minutes=60))
    user.next_check_time = check_time
    await Database.insert_or_replace(user)

    return msg
