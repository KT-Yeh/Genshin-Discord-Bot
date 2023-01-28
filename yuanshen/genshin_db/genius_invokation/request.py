from typing import Any

from ..api import API
from .models import TCGCards


async def fetch_cards() -> TCGCards:
    """取得七聖召喚卡牌的資料，並將資料傳入卡牌模型解析"""

    async def _request(folder: API.GenshinDBFolder) -> Any:
        return await API.request_genshin_db(
            folder, "names", matchCategories=True, verboseCategories=True
        )

    action_cards = await _request(API.GenshinDBFolder.TCG_ACTION_CARDS)
    character_cards = await _request(API.GenshinDBFolder.TCG_CHARACTER_CARDS)
    summons = await _request(API.GenshinDBFolder.TCG_SUMMONS)

    return TCGCards(action_cards, character_cards, summons)
