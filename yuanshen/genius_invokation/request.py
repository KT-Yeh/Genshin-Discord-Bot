import aiohttp
import re
from typing import Optional, Union
from .models import TCGCards

API_URL = "https://sg-hk4e-api-static.hoyoverse.com/event/e20221205drawcard/card_config?lang=zh-tw"


async def fetch_cards() -> Optional[TCGCards]:
    """向 Hoyolab 取得七聖召喚卡牌的資料，並將資料傳入卡牌模型解析"""
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status == 200:
                data: dict = (await response.json(encoding="utf-8"))["data"]
                remove_html_tags(data)
                return TCGCards(data)
            return None


def remove_html_tags(data: Union[dict, list, str, int]):
    """遞迴遍歷整個 json 資料，並移除字串中的 html 標籤"""
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = remove_html_tags(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = remove_html_tags(item)
    elif isinstance(data, str):
        data = re.sub(r"<.*?>", "", data)
        data = data.replace("\\n", "\n")
    return data
