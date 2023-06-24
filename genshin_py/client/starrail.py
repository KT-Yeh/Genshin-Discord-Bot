import genshin

from ..errors_decorator import generalErrorHandler
from .common import get_client


@generalErrorHandler
async def get_starrail_notes(user_id: int) -> genshin.models.StarRailNote:
    client = await get_client(user_id, game=genshin.Game.STARRAIL)
    return await client.get_starrail_notes(client.uid)
