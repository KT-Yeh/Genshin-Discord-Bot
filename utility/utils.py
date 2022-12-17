import logging
import genshin
import re
import json
from typing import Optional
from datetime import datetime
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)


async def trim_cookie(cookie: str) -> Optional[str]:
    """將從 Hoyolab 取得的 Cookie 內容中擷取 ltoken, ltuid, cookie_token 與 account_id，其中 cookie_token 與 account_id 為非必需

    Parameters
    -----
    cookie: `str`
        從 Hoyolab 取得的原始 Cookie 字串

    Returns
    -----
    `str`
        包含 ltoken, ltuid, cookie_token 與 account_id 的字串
    """
    # 嘗試匹配各式 token
    cookie_token = (
        match.group() if (match := re.search("cookie_token=[0-9A-Za-z]{30,}", cookie)) else None
    )
    account_id = match.group() if (match := re.search("account_id=[0-9]{5,}", cookie)) else None
    ltoken = match.group() if (match := re.search("ltoken=[0-9A-Za-z]{30,}", cookie)) else None
    ltuid = match.group() if (match := re.search("ltuid=[0-9]{5,}", cookie)) else None

    cookie_list: list[str] = []
    # 當有 cookie_token 時，嘗試取得 ltoken 並延長 cookie_token 的過期時間，然後回傳完整 cookie 資料
    if cookie_token and account_id:
        try:
            new_cookie = await genshin.complete_cookies(
                f"{cookie_token} {account_id}", refresh=True
            )
            return " ".join(
                [f"{key}={value}" for key, value in new_cookie.items()]
                + [cookie_token, account_id]
            )
        except Exception:  # 失敗則將現有 cookie_token 加到列表
            cookie_list += [cookie_token, account_id]

    # 當有 ltoken 時，加到列表
    if ltoken and ltuid:
        cookie_list += [ltoken, ltuid]

    return None if len(cookie_list) == 0 else " ".join(cookie_list)


def get_server_name(key: str) -> str:
    """從伺服器代號或UID的開頭取得伺服器的名字

    Parameters
    -----
    key: `str`
        伺服器代號或是UID開頭第一位數字

    Returns
    -----
    `str`
        伺服器名字
    """
    return {
        "cn_gf01": "天空島",
        "cn_qd01": "世界樹",
        "os_usa": "美服",
        "os_euro": "歐服",
        "os_asia": "亞服",
        "os_cht": "台港澳服",
        "1": "天空島",
        "2": "天空島",
        "5": "世界樹",
        "6": "美服",
        "7": "歐服",
        "8": "亞服",
        "9": "台港澳服",
    }.get(key, "")


def get_day_of_week(time: datetime) -> str:
    """從時間中取得星期幾的字串，若時間在兩天內則以"今天"、"明天"表示"""
    delta = time.date() - datetime.now().astimezone().date()
    if delta.days == 0:
        return "今天"
    elif delta.days == 1:
        return "明天"
    return {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五", 5: "週六", 6: "週日"}.get(time.weekday(), "")


def get_app_command_mention(name: str) -> str:
    """取得斜線指令的 Mention 格式"""
    if not hasattr(get_app_command_mention, "appcmd_id"):
        try:
            with open("data/app_commands.json", "r", encoding="utf-8") as f:
                setattr(get_app_command_mention, "appcmd_id", json.load(f))
        except Exception:
            get_app_command_mention.appcmd_id = dict()
    id = get_app_command_mention.appcmd_id.get(name)
    return f"</{name}:{id}>" if id is not None else f"`/{name}`"
