import asyncio
from typing import Sequence, Tuple

import genshin

from database import GenshinSpiralAbyss

from ..errors_decorator import generalErrorHandler
from .common import get_client


@generalErrorHandler
async def get_genshin_notes(user_id: int) -> genshin.models.Notes:
    """取得使用者的即時便箋

    Parameters
    ------
    user_id: `int`
        使用者Discord ID

    Returns
    ------
    `Notes`
        查詢結果
    """
    client = await get_client(user_id)
    return await client.get_genshin_notes(client.uid)


@generalErrorHandler
async def get_genshin_spiral_abyss(user_id: int, previous: bool = False) -> GenshinSpiralAbyss:
    """取得深境螺旋資訊

    Parameters
    ------
    user_id: `int`
        使用者Discord ID
    previous: `bool`
        `True`查詢前一期的資訊、`False`查詢本期資訊

    Returns
    ------
    `SpiralAbyssData`
        查詢結果
    """
    client = await get_client(user_id)
    abyss, characters = await asyncio.gather(
        client.get_genshin_spiral_abyss(client.uid or 0, previous=previous),
        client.get_genshin_characters(client.uid or 0),
        return_exceptions=True,
    )
    if isinstance(abyss, BaseException):
        raise abyss
    if isinstance(characters, BaseException):
        return GenshinSpiralAbyss(user_id, abyss.season, abyss, None)
    return GenshinSpiralAbyss(user_id, abyss.season, abyss, characters)


@generalErrorHandler
async def get_genshin_traveler_diary(user_id: int, month: int) -> genshin.models.Diary:
    """取得使用者旅行者札記

    Parameters
    ------
    user_id: `int`
        使用者Discord ID
    month: `int`
        欲查詢的月份

    Returns
    ------
    `Diary`
        查詢結果
    """
    client = await get_client(user_id)
    diary = await client.get_diary(client.uid, month=month)
    return diary


@generalErrorHandler
async def get_genshin_record_card(
    user_id: int,
) -> Tuple[int, genshin.models.PartialGenshinUserStats]:
    """取得使用者記錄卡片(成就、活躍天數、角色數、神瞳、寶箱數...等等)

    Parameters
    ------
    user_id: `int`
        使用者Discord ID

    Returns
    ------
    `(int, PartialGenshinUserStats)`
        查詢結果，包含UID與原神使用者資料
    """
    client = await get_client(user_id)
    userstats = await client.get_partial_genshin_user(client.uid or 0)
    return (client.uid or 0, userstats)


@generalErrorHandler
async def get_genshin_characters(user_id: int) -> Sequence[genshin.models.Character]:
    """取得使用者所有角色資料

    Parameters
    ------
    user_id: `int`
        使用者Discord ID

    Returns
    ------
    `Sequence[Character]`
        查詢結果
    """
    client = await get_client(user_id)
    return await client.get_genshin_characters(client.uid or 0)


@generalErrorHandler
async def get_genshin_notices() -> Sequence[genshin.models.Announcement]:
    """取得遊戲內公告事項

    Returns
    ------
    `Sequence[Announcement]`
        公告事項查詢結果
    """
    client = genshin.Client(lang="zh-tw")
    notices = await client.get_genshin_announcements()
    return notices
