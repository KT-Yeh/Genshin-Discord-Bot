from datetime import datetime, timedelta

import genshin

from database import Database, GenshinScheduleNotes
from utility import EmbedTemplate

from ... import parse_genshin_notes
from .common import CheckResult, cal_next_check_time, get_realtime_notes, get_user


async def check_genshin_notes(user_id: int) -> CheckResult | None:
    """依據每位使用者的設定檢查即時便箋，若超出設定值時則回傳提醒訊息；若跳過此使用者，回傳 None"""
    user = await get_user(user_id, GenshinScheduleNotes)
    if user is None:
        return None

    try:
        notes = await get_realtime_notes(user)
    except Exception as e:
        return CheckResult("原神自動檢查即時便箋時發生錯誤，預計5小時後再檢查。", EmbedTemplate.error(e))

    if not isinstance(notes, genshin.models.Notes):
        return None

    msg = await check_threshold(user, notes)
    embed = await parse_genshin_notes(notes, short_form=True)
    return CheckResult(msg, embed)


async def check_threshold(user: GenshinScheduleNotes, notes: genshin.models.Notes) -> str:
    msg = ""
    next_check_time: list[datetime] = [datetime.now() + timedelta(days=1)]  # 設定一個基本的下次檢查時間
    # 計算下次檢查時間的函式：預計完成時間-使用者設定的時間

    # 檢查樹脂
    if isinstance(user.threshold_resin, int):
        # 當樹脂距離額滿時間低於設定值，則設定要發送的訊息
        if notes.remaining_resin_recovery_time <= timedelta(
            hours=user.threshold_resin, seconds=10
        ):
            msg += (
                "樹脂已經額滿啦！" if notes.remaining_resin_recovery_time <= timedelta(0) else "樹脂快要額滿啦！"
            )
        # 設定下次檢查時間，當樹脂完全額滿時，預計6小時後再檢查；否則依照(預計完成-使用者設定的時間)
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if notes.current_resin >= notes.max_resin
            else cal_next_check_time(notes.remaining_resin_recovery_time, user.threshold_resin)
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
            else cal_next_check_time(
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
            else cal_next_check_time(
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
                "探索派遣已經完成了！" if longest_expedition.remaining_time <= timedelta(0) else "探索派遣快要完成了！"
            )
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if longest_expedition.finished is True
            else cal_next_check_time(longest_expedition.remaining_time, user.threshold_expedition)
        )
    # 檢查每日委託
    if isinstance(user.check_commission_time, datetime):
        # 當現在時間已超過設定的檢查時間
        if datetime.now() >= user.check_commission_time:
            if not notes.claimed_commission_reward:
                msg += "今日的委託任務還未完成！"
            # 下次檢查時間為今天+1天，並更新至資料庫
            user.check_commission_time += timedelta(days=1)
        next_check_time.append(user.check_commission_time)

    # 設定下次檢查時間，從上面設定的時間中取最小的值
    check_time = min(next_check_time)
    # 若此次需要發送訊息，則將下次檢查時間設為至少1小時
    if len(msg) > 0:
        check_time = max(check_time, datetime.now() + timedelta(minutes=60))
    user.next_check_time = check_time
    await Database.insert_or_replace(user)

    return msg
