from typing import Any, Tuple

from .api import API
from .models import (
    Achievements,
    Artifacts,
    Characters,
    Constellations,
    Foods,
    GenshinDbAllData,
    Materials,
    Talents,
    TCGCards,
    Weapons,
)


async def _request(folder: API.GenshinDBFolder) -> Any:
    return await API.request_genshin_db(
        folder, "names", matchCategories=True, verboseCategories=True
    )


async def fetch_cards() -> TCGCards:
    """取得七聖召喚卡牌的資料，並將資料傳入卡牌模型解析"""

    action_cards = await _request(API.GenshinDBFolder.TCG_ACTION_CARDS)
    character_cards = await _request(API.GenshinDBFolder.TCG_CHARACTER_CARDS)
    summons = await _request(API.GenshinDBFolder.TCG_SUMMONS)

    return TCGCards(action_cards, character_cards, summons)


async def fetch_achievements() -> Achievements:
    """取得成就資料，並傳入模型解析"""
    data = await _request(API.GenshinDBFolder.ACHIEVEMENTS)
    return Achievements.parse_obj(data)


async def fetch_characters() -> Tuple[Characters, Constellations, Talents]:
    """取得角色、天賦、命座資料，並傳入模型解析"""
    data = await _request(API.GenshinDBFolder.CHARACTERS)
    characters = Characters.parse_obj(data)

    data = await _request(API.GenshinDBFolder.CONSTELLATIONS)
    constellations = Constellations.parse_obj(data)

    data = await _request(API.GenshinDBFolder.TALENTS)
    talents = Talents.parse_obj(data)

    return characters, constellations, talents


async def fetch_materials() -> Tuple[Materials, Foods]:
    """取得物品、食物資料，並傳入模型解析"""
    data = await _request(API.GenshinDBFolder.MATERIALS)
    materials = Materials.parse_obj(data)

    data = await _request(API.GenshinDBFolder.FOODS)
    foods = Foods.parse_obj(data)

    return materials, foods


async def fetch_equipments() -> Tuple[Artifacts, Weapons]:
    """取得聖遺物、武器資料，並傳入模型解析"""
    data = await _request(API.GenshinDBFolder.ARTIFACTS)
    artifacts = Artifacts.parse_obj(data)

    data = await _request(API.GenshinDBFolder.WEAPONS)
    weapons = Weapons.parse_obj(data)

    return artifacts, weapons


async def fetch_all() -> GenshinDbAllData:
    """取得所有 genshin-db 資料，解析後封裝"""
    tcg_cards = await fetch_cards()
    achievements = await fetch_achievements()
    characters, constellations, talents = await fetch_characters()
    materials, foods = await fetch_materials()
    artifacts, weapons = await fetch_equipments()

    return GenshinDbAllData(
        achievements,
        artifacts,
        characters,
        constellations,
        foods,
        materials,
        talents,
        tcg_cards,
        weapons,
    )
