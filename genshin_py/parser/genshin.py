from typing import Sequence, Union

import discord
import genshin

from database import Database, User
from utility import emoji, get_day_of_week, get_server_name


def parse_genshin_abyss_overview(abyss: genshin.models.SpiralAbyss) -> discord.Embed:
    """解析深淵概述資料，包含日期、層數、戰鬥次數、總星數...等等

    ------
    Parameters
    abyss `SpiralAbyss`: 深境螺旋資料
    ------
    Returns
    `discord.Embed`: discord嵌入格式
    """
    result = discord.Embed(
        description=(
            f'第 {abyss.season} 期：{abyss.start_time.astimezone().strftime("%Y.%m.%d")} ~ '
            f'{abyss.end_time.astimezone().strftime("%Y.%m.%d")}'
        ),
        color=0x6959C1,
    )

    crowned: bool = (
        True
        if abyss.max_floor == "12-3" and abyss.total_stars == 36 and abyss.total_battles == 12
        else False
    )

    def get_character_rank(c: Sequence[genshin.models.AbyssRankCharacter]):
        return " " if len(c) == 0 else f"{c[0].name}：{c[0].value}"

    result.add_field(
        name=f'最深抵達：{abyss.max_floor}　戰鬥次數：{"👑 (12)" if crowned else abyss.total_battles}　★：{abyss.total_stars}',
        value=f"[最多擊破數] {get_character_rank(abyss.ranks.most_kills)}\n"
        f"[最強之一擊] {get_character_rank(abyss.ranks.strongest_strike)}\n"
        f"[受最多傷害] {get_character_rank(abyss.ranks.most_damage_taken)}\n"
        f"[Ｑ施放次數] {get_character_rank(abyss.ranks.most_bursts_used)}\n"
        f"[Ｅ施放次數] {get_character_rank(abyss.ranks.most_skills_used)}",
        inline=False,
    )
    return result


def parse_genshin_abyss_chamber(chamber: genshin.models.Chamber) -> str:
    """取得深淵某一間的角色名字

    ------
    Parameters
    chamber `Chamber`: 深淵某一間的資料
    ------
    Returns
    `str`: 角色名字組成的字串
    """
    chara_list: list[list[str]] = [[], []]  # 分成上下半間
    for i, battle in enumerate(chamber.battles):
        for chara in battle.characters:
            chara_list[i].append(chara.name)
    return f'{".".join(chara_list[0])} ／\n{".".join(chara_list[1])}'


def parse_genshin_character(character: genshin.models.Character) -> discord.Embed:
    """解析角色，包含命座、等級、好感、武器、聖遺物

    ------
    Parameters
    character `Character`: 人物資料
    ------
    Returns
    `discord.Embed`: discord嵌入格式
    """
    color = {
        "pyro": 0xFB4120,
        "electro": 0xBF73E7,
        "hydro": 0x15B1FF,
        "cryo": 0x70DAF1,
        "dendro": 0xA0CA22,
        "anemo": 0x5CD4AC,
        "geo": 0xFAB632,
    }
    embed = discord.Embed(color=color.get(character.element.lower()))
    embed.set_thumbnail(url=character.icon)
    embed.add_field(
        name=f"★{character.rarity} {character.name}",
        inline=True,
        value=f"命座：{character.constellation}\n等級：Lv. {character.level}\n好感：Lv. {character.friendship}",
    )

    weapon = character.weapon
    embed.add_field(
        name=f"★{weapon.rarity} {weapon.name}",
        inline=True,
        value=f"精煉：{weapon.refinement} 階\n等級：Lv. {weapon.level}",
    )

    if character.constellation > 0:
        number = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}
        msg = "\n".join(
            [
                f"第{number[constella.pos]}層：{constella.name}"
                for constella in character.constellations
                if constella.activated
            ]
        )
        embed.add_field(name="命之座", inline=False, value=msg)

    if len(character.artifacts) > 0:
        msg = "\n".join(
            [
                f"{artifact.pos_name}：{artifact.name} ({artifact.set.name})"
                for artifact in character.artifacts
            ]
        )
        embed.add_field(name="聖遺物", inline=False, value=msg)

    return embed


def parse_genshin_diary(diary: genshin.models.Diary, month: int) -> discord.Embed:
    """解析旅行者日誌

    ------
    Parameters
    diary `Diary`: 旅行者日誌
    ------
    Returns
    `discord.Embed`: discord嵌入格式
    """
    d = diary.data
    embed = discord.Embed(
        title=f"{diary.nickname} 的旅行者札記：{month}月",
        description=f'原石收入比上個月{"增加" if d.current_primogems >= d.last_primogems else "減少"}了{abs(d.primogems_rate)}%，'
        f'摩拉收入比上個月{"增加" if d.current_mora >= d.last_mora else "減少"}了{abs(d.mora_rate)}%',
        color=0xFD96F4,
    )
    embed.add_field(
        name="當月共獲得",
        value=f"{emoji.items.primogem}原石：{d.current_primogems} ({round(d.current_primogems/160)}{emoji.items.intertwined_fate})\n"
        f'{emoji.items.mora}摩拉：{format(d.current_mora, ",")}',
    )
    embed.add_field(
        name="上個月獲得",
        value=f"{emoji.items.primogem}原石：{d.last_primogems} ({round(d.last_primogems/160)}{emoji.items.intertwined_fate})\n"
        f'{emoji.items.mora}摩拉：{format(d.last_mora, ",")}',
    )
    embed.add_field(name="\u200b", value="\u200b")  # 空白行

    # 將札記原石組成平分成兩個field
    for i in range(0, 2):
        msg = ""
        length = len(d.categories)
        for j in range(round(length / 2 * i), round(length / 2 * (i + 1))):
            msg += f"{d.categories[j].name[0:2]}：{d.categories[j].amount} ({d.categories[j].percentage}%)\n"
        embed.add_field(name=f"原石收入組成 {i+1}", value=msg, inline=True)

    embed.add_field(name="\u200b", value="\u200b")  # 空白行

    return embed


async def parse_genshin_notes(
    notes: genshin.models.Notes,
    *,
    user: Union[discord.User, discord.Member, None] = None,
    shortForm: bool = False,
) -> discord.Embed:
    """解析即時便箋的資料，將內容排版成discord嵌入格式回傳

    ------
    Parameters
    notes `Notes`: 即時便箋的資料
    user `discord.User`: Discord使用者
    shortForm `bool`: 設為`False`，完整顯示樹脂、寶錢、參數質變儀、派遣、每日、週本；設為`True`，只顯示樹脂、寶錢、參數質變儀
    ------
    Returns
    `discord.Embed`: discord嵌入格式
    """
    # 原粹樹脂
    resin_title = f"{emoji.notes.resin}當前原粹樹脂：{notes.current_resin}/{notes.max_resin}\n"
    if notes.current_resin >= notes.max_resin:
        recover_time = "已額滿！"
    else:
        day_msg = get_day_of_week(notes.resin_recovery_time)
        recover_time = f'{day_msg} {notes.resin_recovery_time.strftime("%H:%M")}'
    resin_msg = f"{emoji.notes.resin}全部恢復時間：{recover_time}\n"
    # 每日、週本
    resin_msg += f"{emoji.notes.commission}每日委託任務："
    resin_msg += (
        "獎勵已領\n"
        if notes.claimed_commission_reward is True
        else "**尚未領獎**\n"
        if notes.max_commissions == notes.completed_commissions
        else f"剩餘 {notes.max_commissions - notes.completed_commissions} 個\n"
    )
    if not shortForm:
        resin_msg += (
            f"{emoji.notes.enemies_of_note}週本樹脂減半：剩餘 {notes.remaining_resin_discounts} 次\n"
        )
    # 洞天寶錢恢復時間
    resin_msg += f"{emoji.notes.realm_currency}當前洞天寶錢：{notes.current_realm_currency}/{notes.max_realm_currency}\n"
    if not shortForm and notes.max_realm_currency > 0:
        if notes.current_realm_currency >= notes.max_realm_currency:
            recover_time = "已額滿！"
        else:
            day_msg = get_day_of_week(notes.realm_currency_recovery_time)
            recover_time = f'{day_msg} {notes.realm_currency_recovery_time.strftime("%H:%M")}'
        resin_msg += f"{emoji.notes.realm_currency}全部恢復時間：{recover_time}\n"
    # 參數質變儀剩餘時間
    if (t := notes.remaining_transformer_recovery_time) is not None:
        if t.days > 0:
            recover_time = f"剩餘 {t.days} 天"
        elif t.hours > 0:
            recover_time = f"剩餘 {t.hours} 小時"
        elif t.minutes > 0:
            recover_time = f"剩餘 {t.minutes} 分"
        elif t.seconds > 0:
            recover_time = f"剩餘 {t.seconds} 秒"
        else:
            recover_time = "可使用"
        resin_msg += f"{emoji.notes.transformer}參數質變儀　：{recover_time}\n"
    # 探索派遣剩餘時間
    exped_finished = 0
    exped_msg = ""
    for expedition in notes.expeditions:
        exped_msg += f"． {expedition.character.name}："
        if expedition.finished:
            exped_finished += 1
            exped_msg += "已完成\n"
        else:
            day_msg = get_day_of_week(expedition.completion_time)
            exped_msg += f'{day_msg} {expedition.completion_time.strftime("%H:%M")}\n'

    exped_title = f"{emoji.notes.expedition}探索派遣結果：{exped_finished}/{len(notes.expeditions)}\n"

    # 根據樹脂數量，以80作分界，embed顏色從綠色(0x28c828)漸變到黃色(0xc8c828)，再漸變到紅色(0xc82828)
    r = notes.current_resin
    color = (
        0x28C828 + 0x010000 * int(0xA0 * r / 80)
        if r < 80
        else 0xC8C828 - 0x000100 * int(0xA0 * (r - 80) / 80)
    )
    embed = discord.Embed(color=color)

    if (not shortForm) and (exped_msg != ""):
        embed.add_field(name=resin_title, value=resin_msg)
        embed.add_field(name=exped_title, value=exped_msg)
    else:
        embed.add_field(name=resin_title, value=(resin_msg + exped_title))

    if user is not None:
        _u = await Database.select_one(User, User.discord_id.is_(user.id))
        uid = str(_u.uid_genshin if _u else "")
        embed.set_author(name=f"{get_server_name(uid[0])} {uid}", icon_url=user.display_avatar.url)
    return embed
