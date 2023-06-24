import discord
import genshin

from database import Database, User
from utility import emoji, get_day_of_week, get_server_name


async def parse_starrail_notes(
    notes: genshin.models.StarRailNote,
    user: discord.User | discord.Member | None = None,
) -> discord.Embed:
    # 開拓力
    stamina_title = f"當前開拓力：{notes.current_stamina}/{notes.max_stamina}\n"
    if notes.current_stamina >= notes.max_stamina:
        recovery_time = "已額滿！"
    else:
        day_msg = get_day_of_week(notes.stamina_recovery_time)
        recovery_time = f"{day_msg} {notes.stamina_recovery_time.strftime('%H:%M')}"
    stamina_msg = f"全部恢復時間：{recovery_time}"

    # 委託執行
    exped_finished = 0
    exped_msg = ""
    for expedition in notes.expeditions:
        exped_msg += f"． {expedition.name}："
        if expedition.finished is True:
            exped_finished += 1
            exped_msg += "已完成\n"
        else:
            day_msg = get_day_of_week(expedition.completion_time)
            exped_msg += f"{day_msg} {expedition.completion_time.strftime('%H:%M')}\n"
    exped_title = f"委託執行：{exped_finished}/{len(notes.expeditions)}"

    # 根據開拓力數量，以 90 作分界，embed 顏色從綠色 (0x28c828) 漸變到黃色 (0xc8c828)，再漸變到紅色 (0xc82828)
    stamina = notes.current_stamina
    color = (
        0x28C828 + 0x010000 * int(0xA0 * stamina / 90)
        if stamina < 90
        else 0xC8C828 - 0x000100 * int(0xA0 * (stamina - 90) / 90)
    )

    embed = discord.Embed(color=color)
    embed.add_field(name=stamina_title, value=stamina_msg, inline=False)
    embed.add_field(name=exped_title, value=exped_msg, inline=False)

    if user is not None:
        _u = await Database.select_one(User, User.discord_id.is_(user.id))
        uid = str(_u.uid_starrail if _u else "")
        embed.set_author(
            name=f"鐵道 {get_server_name(uid[0])} {uid}",
            icon_url=user.display_avatar.url,
        )
    return embed
