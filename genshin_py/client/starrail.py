import genshin

from ..errors_decorator import generalErrorHandler
from .common import get_client


@generalErrorHandler
async def get_starrail_notes(user_id: int) -> genshin.models.StarRailNote:
    client = await get_client(user_id, game=genshin.Game.STARRAIL)
    return await client.get_starrail_notes(client.uid)


@generalErrorHandler
async def get_starrail_diary(user_id: int, month: int) -> genshin.models.StarRailDiary:
    client = await get_client(user_id, game=genshin.Game.STARRAIL)
    return await client.get_starrail_diary(client.uid, month=month)


@generalErrorHandler
async def get_starrail_characters(user_id: int) -> list[genshin.models.StarRailDetailCharacter]:
    client = await get_client(user_id, game=genshin.Game.STARRAIL)
    r = await client.get_starrail_characters(client.uid)
    return r.avatar_list


@generalErrorHandler
async def get_starrail_forgottenhall(
    user_id: int, previous_season: bool = False
) -> genshin.models.StarRailChallenge:
    client = await get_client(user_id, game=genshin.Game.STARRAIL)
    return await client.get_starrail_challenge(client.uid, previous=previous_season)


@generalErrorHandler
async def get_starrail_pure_fiction(
    user_id: int, previous_season: bool = False
) -> genshin.models.StarRailPureFiction:
    client = await get_client(user_id, game=genshin.Game.STARRAIL)
    return await client.get_starrail_pure_fiction(client.uid, previous=previous_season)


@generalErrorHandler
async def get_starrail_userstats(user_id: int) -> genshin.models.StarRailUserStats:
    client = await get_client(user_id, game=genshin.Game.STARRAIL)
    return await client.get_starrail_user(client.uid)
