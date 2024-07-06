import json
import logging
from datetime import datetime

from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)


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
        "prod_official_usa": "美服",
        "prod_official_euro": "歐服",
        "prod_official_asia": "亞服",
        "prod_official_cht": "台港澳服",
        "prod_gf_usa": "美服",
        "prod_gf_eu": "歐服",
        "prod_gf_jp": "亞服",
        "prod_gf_sg": "台港澳服",
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
    return {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五", 5: "週六", 6: "週日"}.get(
        time.weekday(), ""
    )


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
