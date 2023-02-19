import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from .api import EnkaAPI, EnkaError


async def fetch_enka_data(
    uid: int, cache_data: Optional[Dict[str, Any]] = None, retry: int = 1
) -> Dict[str, Any]:
    """從API取得玩家的角色展示櫃資料，與舊資料合併後回傳

    Paramters
    ------
    uid: `int`
        使用者遊戲 UID
    cache_data: `Optional[Dict[str, Any]]`
        使用者上次存在資料庫內的快取資料
    retry: `int` = 1
        向 enka.network API 請求失敗後的重試次數

    Returns
    ------
    `Dict[str, Any]`
        將從 API 取得的資料

    """
    async with aiohttp.request(
        "GET",
        EnkaAPI.get_user_data_url(uid),
        headers={"User-Agent": "KT-Yeh/Genshin-Discord-Bot"},
    ) as resp:
        if resp.status == 200:
            resp_data: Dict[str, Any] = await resp.json()
            # 為了減少無效的重複請求，在此設定時間戳、合併快取資料並保存資料至資料庫
            resp_data["timestamp"] = int(datetime.now().timestamp())
            raw_data = (
                _combine_cache_data(resp_data, cache_data) if cache_data is not None else resp_data
            )
            return raw_data
        else:  # 無法從 API 取得資料時
            match resp.status:  # 先檢查跟使用者有關的錯誤
                case 400:
                    raise EnkaError.WrongUIDFormat()
                case 404:
                    raise EnkaError.PlayerNotExist()
            if retry > 0:  # 再次嘗試直到重試次數歸零
                await asyncio.sleep(0.5)
                return await fetch_enka_data(uid, cache_data, retry=retry - 1)
            else:
                match resp.status:
                    case 429:
                        raise EnkaError.RateLimit()
                    case 424:
                        raise EnkaError.Maintenance()
                    case 500, 503:
                        raise EnkaError.ServerError()
                    case _:
                        raise EnkaError.GeneralError()


def _combine_cache_data(new_data: Dict[str, Any], cache_data: Dict[str, Any]) -> Dict[str, Any]:
    """將快取資料合併到新取得的資料

    Parameters
    ------
    new_data: `Dict[str, Any]`
        從 API 回傳的最新資料
    cache_data: `Dict[str, Any]`
        之前保存在資料庫的快取資料

    Returns
    ------
    `Dict[str, Any]`
        回傳合併後的資料
    """
    # 確認合併後showAvatarInfoList與avatarInfoList長度相等
    len_new_showAvatar = len(new_data["playerInfo"].get("showAvatarInfoList", []))
    len_cache_showAvatar = len(cache_data["playerInfo"].get("showAvatarInfoList", []))
    len_new_avatarInfo = len(new_data.get("avatarInfoList", []))
    len_cache_avatarInfo = len(cache_data.get("avatarInfoList", []))
    if len_new_showAvatar + len_cache_showAvatar != len_new_avatarInfo + len_cache_avatarInfo:
        return new_data

    def combine_list(new_list: List[Dict[str, Any]], cache_list: List[Dict[str, Any]]):
        for cache_avatarInfo in cache_list:
            if len(new_list) >= 23:  # 因應Discord下拉選單的上限，在此只保留23名角色
                break
            # 若新資料與快取資料有相同角色，則保留新資料；其他角色從快取資料加入到新資料裡面
            for new_avatarInfo in new_list:
                if new_avatarInfo["avatarId"] == cache_avatarInfo["avatarId"]:
                    break
            else:
                new_list.append(cache_avatarInfo)

    if "showAvatarInfoList" in cache_data["playerInfo"]:
        if "showAvatarInfoList" not in new_data["playerInfo"]:
            new_data["playerInfo"]["showAvatarInfoList"] = []
        combine_list(
            new_data["playerInfo"]["showAvatarInfoList"],
            cache_data["playerInfo"]["showAvatarInfoList"],
        )

    if "avatarInfoList" in cache_data:
        if "avatarInfoList" not in new_data:
            new_data["avatarInfoList"] = []
        combine_list(new_data["avatarInfoList"], cache_data["avatarInfoList"])

    return new_data
