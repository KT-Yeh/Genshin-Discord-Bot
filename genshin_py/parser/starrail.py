from datetime import datetime

import discord
import genshin

from database import Database, User
from utility import get_day_of_week, get_server_name


async def parse_starrail_notes(
    notes: genshin.models.StarRailNote,
    user: discord.User | discord.Member | None = None,
    *,
    short_form: bool = False,
) -> discord.Embed:
    """解析即時便箋的資料，將內容排版成 discord 嵌入格式回傳"""
    # 開拓力
    stamina_title = f"當前開拓力：{notes.current_stamina}/{notes.max_stamina}"
    if notes.current_reserve_stamina > 0:
        stamina_title += f" + {notes.current_reserve_stamina}"
    if notes.current_stamina >= notes.max_stamina:
        recovery_time = "已額滿！"
    else:
        day_msg = get_day_of_week(notes.stamina_recovery_time)
        recovery_time = f"{day_msg} {notes.stamina_recovery_time.strftime('%H:%M')}"
    stamina_msg = f"恢復時間：{recovery_time}\n"

    # 每日、模擬宇宙、周本
    stamina_msg += f"每日實訓：{notes.current_train_score} / {notes.max_train_score}\n"
    stamina_msg += f"模擬宇宙：{notes.current_rogue_score} / {notes.max_rogue_score}\n"
    stamina_msg += f"歷戰餘響：剩餘 {notes.remaining_weekly_discounts} 次\n"

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
    # 簡約格式只留最久的完成時間
    if short_form is True and len(notes.expeditions) > 0:
        longest_expedition = max(notes.expeditions, key=lambda epd: epd.remaining_time)
        if longest_expedition.finished is True:
            exped_msg = "． 完成時間：已完成\n"
        else:
            day_msg = get_day_of_week(longest_expedition.completion_time)
            exped_msg = (
                f"． 完成時間：{day_msg} {longest_expedition.completion_time.strftime('%H:%M')}\n"
            )

    exped_title = f"委託執行：{exped_finished}/{len(notes.expeditions)}"

    # 根據開拓力數量，以一半作分界，embed 顏色從綠色 (0x28c828) 漸變到黃色 (0xc8c828)，再漸變到紅色 (0xc82828)
    stamina = notes.current_stamina
    max_half = notes.max_stamina / 2
    color = (
        0x28C828 + 0x010000 * int(0xA0 * stamina / max_half)
        if stamina < max_half
        else 0xC8C828 - 0x000100 * int(0xA0 * (stamina - max_half) / max_half)
    )

    embed = discord.Embed(color=color)
    embed.add_field(name=stamina_title, value=stamina_msg, inline=False)
    if exped_msg != "":
        embed.add_field(name=exped_title, value=exped_msg, inline=False)

    if user is not None:
        _u = await Database.select_one(User, User.discord_id.is_(user.id))
        uid = str(_u.uid_starrail if _u else "")
        embed.set_author(
            name=f"鐵道 {get_server_name(uid[0])} {uid}",
            icon_url=user.display_avatar.url,
        )
    return embed


def parse_starrail_diary(diary: genshin.models.StarRailDiary, month: int) -> discord.Embed:
    ...


def parse_starrail_character(character: genshin.models.StarRailDetailCharacter) -> discord.Embed:
    """解析角色，包含星魂、等級、光錐、遺物"""
    color = {
        "physical": 0xC5C5C5,
        "fire": 0xF4634E,
        "ice": 0x72C2E6,
        "lightning": 0xDC7CF4,
        "wind": 0x73D4A4,
        "quantum": 0x9590E4,
        "imaginary": 0xF7E54B,
    }
    embed = discord.Embed(color=color.get(character.element.lower()))
    embed.set_thumbnail(url=character.icon)
    embed.add_field(
        name=f"★{character.rarity} {character.name}",
        inline=True,
        value=f"星魂：{character.rank}\n等級：Lv. {character.level}",
    )
    if character.equip:
        lightcone = character.equip
        embed.add_field(
            name=f"光錐：{lightcone.name}",
            inline=True,
            value=f"疊影：{lightcone.rank} 階\n等級：Lv. {lightcone.level}",
        )

    if character.rank > 0:
        number = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}
        msg = "\n".join(
            [f"第{number[rank.pos]}層：{rank.name}" for rank in character.ranks if rank.is_unlocked]
        )
        embed.add_field(name="星魂", inline=False, value=msg)

    if len(character.relics) > 0:
        pos_name = {1: "頭部", 2: "手部", 3: "軀幹", 4: "腳部"}
        msg = "\n".join(
            [
                f"{pos_name.get(relic.pos)}：★{relic.rarity} {relic.name}"
                for relic in character.relics
            ]
        )
        embed.add_field(name="遺器", inline=False, value=msg)

    if len(character.ornaments) > 0:
        pos_name = {5: "次元球", 6: "連結繩"}
        msg = "\n".join(
            [
                f"{pos_name.get(ornament.pos)}：★{ornament.rarity} {ornament.name}"
                for ornament in character.ornaments
            ]
        )
        embed.add_field(name="飾品", inline=False, value=msg)
    return embed


def parse_starrail_hall_overview(
    hall: genshin.models.StarRailChallenge | genshin.models.StarRailPureFiction,
) -> discord.Embed:
    """解析星穹鐵道忘卻之庭概述資料，包含關卡進度、戰鬥次數、獲得星數、期數"""
    # 檢查皇冠資格
    has_crown: bool = False
    if isinstance(hall, genshin.models.StarRailChallenge):
        # 忘卻之庭 2023/12/20 前為 10 層，之後為 12 層
        max_stars = 30 if hall.begin_time.datetime < datetime(2023, 12, 20) else 36
        if hall.total_stars == max_stars:
            non_skip_battles = [floor.is_quick_clear for floor in hall.floors].count(False)
            has_crown = hall.total_battles == non_skip_battles
    else:  # isinstance(hall, genshin.models.StarRailPureFiction)
        if hall.total_stars == 12:
            non_skip_battles = [floor.is_quick_clear for floor in hall.floors].count(False)
            has_crown = hall.total_battles == non_skip_battles
    battle_nums = f"👑 ({hall.total_battles})" if has_crown else hall.total_battles

    desc: str = (
        f"{hall.begin_time.datetime.strftime('%Y.%m.%d')} ~ {hall.end_time.datetime.strftime('%Y.%m.%d')}\n"
    )
    desc += f"關卡進度：{hall.max_floor}\n"
    desc += f"戰鬥次數：{battle_nums}　★：{hall.total_stars}\n"
    embed = discord.Embed(description=desc, color=0x934151)
    return embed
