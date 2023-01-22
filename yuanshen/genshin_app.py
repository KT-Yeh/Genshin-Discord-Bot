import asyncio
from typing import Sequence, Tuple

import genshin
import sentry_sdk

from data.database import SpiralAbyssData, User, db
from utility import LOG, get_app_command_mention, trim_cookie

from .errors import UserDataNotFound, generalErrorHandler


@generalErrorHandler
async def set_cookie(user_id: int, cookie: str) -> str:
    """設定使用者Cookie

    Parameters
    ------
    user_id: `int`
        使用者Discord ID
    cookie: `str`
        Hoyolab cookie

    Returns
    ------
    `str`
        回覆給使用者的訊息
    """
    LOG.Info(f"設定 {LOG.User(user_id)} 的Cookie：{cookie}")
    trimed_cookie = await trim_cookie(cookie)
    if trimed_cookie is None:
        return f'錯誤或無效的Cookie，請重新輸入(使用 {get_app_command_mention("cookie設定")} 顯示說明)'
    client = genshin.Client(lang="zh-tw")
    client.set_cookies(trimed_cookie)
    # 先以國際服 client 取得帳號資訊，若失敗則嘗試使用中國服 client
    try:
        accounts = await client.get_game_accounts()
    except genshin.errors.InvalidCookies:
        client.region = genshin.Region.CHINESE
        accounts = await client.get_game_accounts()

    # 篩選出帳號內原神角色
    accounts = [account for account in accounts if account.game == genshin.types.Game.GENSHIN]
    if len(accounts) == 0:
        LOG.Info(f"{LOG.User(user_id)} 帳號內沒有任何角色")
        result = "帳號內沒有任何原神角色，取消設定Cookie"
    else:
        await db.users.add(User(id=user_id, cookie=trimed_cookie))
        LOG.Info(f"{LOG.User(user_id)} Cookie設置成功")

        if len(accounts) == 1 and len(str(accounts[0].uid)) == 9:
            await db.users.update(user_id, uid=accounts[0].uid)
            result = f"Cookie已設定完成，角色UID: {accounts[0].uid} 已保存！"
        else:
            result = f'Cookie已保存，你的Hoyolab帳號內共有{len(accounts)}名角色\n請使用 {get_app_command_mention("uid設定")} 指定要保存的原神角色'
    return result


@generalErrorHandler
async def get_game_accounts(user_id: int) -> Sequence[genshin.models.GenshinAccount]:
    """取得同一個Hoyolab帳號下，各伺服器的原神帳號

    Parameters
    ------
    user_id: `int`
        使用者Discord ID

    Returns
    ------
    `Sequence[GenshinAccount]`
        查詢結果
    """
    client = await get_genshin_client(user_id, check_uid=False)
    accounts = await client.get_game_accounts()
    return [account for account in accounts if account.game == genshin.types.Game.GENSHIN]


@generalErrorHandler
async def get_realtime_notes(user_id: int, *, schedule=False) -> genshin.models.Notes:
    """取得使用者的即時便箋

    Parameters
    ------
    user_id: `int`
        使用者Discord ID
    schedule: `bool`
        是否為排程檢查樹脂

    Returns
    ------
    `Notes`
        查詢結果
    """
    client = await get_genshin_client(user_id, update_using_time=(not schedule))
    return await client.get_genshin_notes(client.uid)


@generalErrorHandler
async def redeem_code(user_id: int, code: str) -> str:
    """為使用者使用指定的兌換碼

    Parameters
    ------
    user_id:`int`
        使用者Discord ID
    code: `str`
        Hoyolab兌換碼

    Returns
    ------
    `str`
        回覆給使用者的訊息
    """
    client = await get_genshin_client(user_id)
    await client.redeem_code(code, client.uid)
    return "兌換碼使用成功！"


async def claim_daily_reward(user_id: int, *, honkai: bool = False, schedule=False) -> str:
    """為使用者在Hoyolab簽到

    Parameters
    ------
    user_id: `int`
        使用者Discord ID
    honkai: `bool`
        是否也簽到崩壞3
    schedule: `bool`
        是否為排程自動簽到

    Returns
    ------
    `str`
        回覆給使用者的訊息
    """
    try:
        client = await get_genshin_client(user_id, update_using_time=(not schedule))
    except Exception as e:
        return str(e)

    game_name = {genshin.Game.GENSHIN: "原神", genshin.Game.HONKAI: "崩壞3"}

    async def claim_reward(game: genshin.Game, retry: int = 5) -> str:
        try:
            reward = await client.claim_daily_reward(game=game)
        except genshin.errors.AlreadyClaimed:
            return f"{game_name[game]}今日獎勵已經領過了！"
        except genshin.errors.InvalidCookies:
            return "Cookie已失效，請從Hoyolab重新取得新Cookie"
        except Exception as e:
            if (
                isinstance(e, genshin.errors.GenshinException)
                and e.retcode == -10002
                and game == genshin.Game.HONKAI
            ):
                return "崩壞3簽到失敗，未查詢到角色資訊，請確認艦長是否已綁定新HoYoverse通行證"

            LOG.FuncExceptionLog(user_id, "claimDailyReward", e)
            if retry > 0:
                await asyncio.sleep(1)
                return await claim_reward(game, retry - 1)

            LOG.Error(f"{LOG.User(user_id)} {game_name[game]}簽到失敗")
            sentry_sdk.capture_exception(e)
            return f"{game_name[game]}簽到失敗：{e}"
        else:
            return f"{game_name[game]}今日簽到成功，獲得 {reward.amount}x {reward.name}！"

    result = await claim_reward(genshin.Game.GENSHIN)
    if honkai:
        result = result + " " + await claim_reward(genshin.Game.HONKAI)

    # Hoyolab社群簽到
    try:
        await client.check_in_community()
    except genshin.errors.GenshinException as e:
        if e.retcode != 2001:
            LOG.FuncExceptionLog(user_id, "claimDailyReward: Hoyolab", e)
    except Exception as e:
        LOG.FuncExceptionLog(user_id, "claimDailyReward: Hoyolab", e)

    return result


@generalErrorHandler
async def get_spiral_abyss(user_id: int, previous: bool = False) -> SpiralAbyssData:
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
    client = await get_genshin_client(user_id)
    # 為了刷新戰鬥數據榜，需要先對record card發出請求
    await client.get_record_cards()
    abyss, characters = await asyncio.gather(
        client.get_genshin_spiral_abyss(client.uid or 0, previous=previous),
        client.get_genshin_characters(client.uid or 0),
        return_exceptions=True,
    )
    if isinstance(abyss, BaseException):
        raise abyss
    if isinstance(characters, BaseException):
        return SpiralAbyssData(user_id, abyss, characters=None)
    return SpiralAbyssData(user_id, abyss, characters=characters)


@generalErrorHandler
async def get_traveler_diary(user_id: int, month: int) -> genshin.models.Diary:
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
    client = await get_genshin_client(user_id)
    diary = await client.get_diary(client.uid, month=month)
    return diary


@generalErrorHandler
async def get_record_card(user_id: int) -> Tuple[int, genshin.models.PartialGenshinUserStats]:
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
    client = await get_genshin_client(user_id)
    userstats = await client.get_partial_genshin_user(client.uid or 0)
    return (client.uid or 0, userstats)


@generalErrorHandler
async def get_characters(user_id: int) -> Sequence[genshin.models.Character]:
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
    client = await get_genshin_client(user_id)
    return await client.get_genshin_characters(client.uid or 0)


@generalErrorHandler
async def get_game_notices() -> Sequence[genshin.models.Announcement]:
    """取得遊戲內公告事項

    Returns
    ------
    `Sequence[Announcement]`
        公告事項查詢結果
    """
    client = genshin.Client(lang="zh-tw")
    notices = await client.get_genshin_announcements()
    return notices


async def get_genshin_client(
    user_id: int, *, check_uid=True, update_using_time: bool = True
) -> genshin.Client:
    """設定並取得原神API的Client

    Parameters
    ------
    user_id: `int`
        使用者Discord ID
    check_uid: `bool`
        是否檢查UID
    update_using_time: `bool`
        是否更新使用者最後使用時間

    Returns
    ------
    `genshin.Client`
        原神API的Client
    """
    user = await db.users.get(user_id)
    check, msg = await db.users.exist(
        user, check_uid=check_uid, update_using_time=update_using_time
    )
    if check is False or user is None:
        raise UserDataNotFound(msg)

    if user.uid is not None and str(user.uid)[0] in ["1", "2", "5"]:
        client = genshin.Client(region=genshin.Region.CHINESE, lang="zh-cn")
    else:
        client = genshin.Client(lang="zh-tw")
    client.set_cookies(user.cookie)
    client.default_game = genshin.Game.GENSHIN
    client.uid = user.uid if user.uid else 0
    return client
