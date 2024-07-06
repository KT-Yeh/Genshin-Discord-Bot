import discord
import genshin

from database import Database, User
from utility import get_day_of_week


async def parse_zzz_notes(
    notes: genshin.models.ZZZNotes,
    user: discord.User | discord.Member | None = None,
) -> discord.Embed:
    """解析即時便箋的資料，將內容排版成 discord 嵌入格式回傳"""
    # 電量
    battery_title = f"當前電量：{notes.battery_charge.current}/{notes.battery_charge.max}"
    if notes.battery_charge.is_full:
        recovery_time = "已充滿！"
    else:
        day_msg = get_day_of_week(notes.battery_charge.full_datetime)
        recovery_time = f"{day_msg} {notes.battery_charge.full_datetime.strftime('%H:%M')}"
    battery_msg = f"恢復時間：{recovery_time}\n"

    video_state_map = {
        genshin.models.VideoStoreState.REVENUE_AVAILABLE: "待結算",
        genshin.models.VideoStoreState.WAITING_TO_OPEN: "等待營業",
        genshin.models.VideoStoreState.CURRENTLY_OPEN: "正在營業",
    }
    battery_msg += f"每日活躍：{notes.engagement.current}/{notes.engagement.max}\n"
    battery_msg += f"刮刮樂　：{'已完成' if notes.scratch_card_completed else '未完成'}\n"
    battery_msg += f"錄影帶店：{video_state_map.get(notes.video_store_state, '')}\n"

    # 根據電量數量，以一半作分界，embed 顏色從綠色 (0x28c828) 漸變到黃色 (0xc8c828)，再漸變到紅色 (0xc82828)
    battery = notes.battery_charge.current
    max_half = notes.battery_charge.max / 2
    color = (
        0x28C828 + 0x010000 * int(0xA0 * battery / max_half)
        if battery < max_half
        else 0xC8C828 - 0x000100 * int(0xA0 * (battery - max_half) / max_half)
    )

    embed = discord.Embed(color=color)
    embed.add_field(name=battery_title, value=battery_msg, inline=False)

    if user is not None:
        _u = await Database.select_one(User, User.discord_id.is_(user.id))
        uid = str(_u.uid_zzz if _u else "")
        embed.set_author(
            name=f"絕區零 {uid}",
            icon_url=user.display_avatar.url,
        )
    return embed
