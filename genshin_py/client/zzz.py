import genshin

from ..errors_decorator import generalErrorHandler
from .common import get_client


@generalErrorHandler
async def get_zzz_notes(user_id: int) -> genshin.models.ZZZNotes:
    client = await get_client(user_id, game=genshin.Game.ZZZ)
    return await client.get_zzz_notes(client.uid)
