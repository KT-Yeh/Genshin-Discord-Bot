import asyncio
from typing import Sequence, Tuple

import genshin
import sentry_sdk

import database
from database import Database, GenshinSpiralAbyss, User
from utility import LOG, get_app_command_mention

from .errors import UserDataNotFound
from .errors_decorator import generalErrorHandler


@generalErrorHandler
async def set_cookie(user_id: int, cookie: str, games: Sequence[genshin.Game]) -> str:
    """根據遊戲設定使用者 Cookie

    Parameters
    ------
    user_id: `int`
        使用者Discord ID
    cookie: `str`
        Hoyolab cookie
    games: `Sequence[genshin.Game]`
        要設定哪些遊戲的 cookie

    Returns
    ------
    `str`
        回覆給使用者的訊息
    """
    LOG.Info(f"設定 {LOG.User(user_id)} 的Cookie：{cookie}")

    client = genshin.Client(lang="zh-tw")
    client.set_cookies(cookie)

    # 先以國際服 client 取得帳號資訊，若失敗則嘗試使用中國服 client
    try:
        accounts = await client.get_game_accounts()
    except genshin.errors.InvalidCookies:
        client.region = genshin.Region.CHINESE
        accounts = await client.get_game_accounts()
    gs_accounts = [a for a in accounts if a.game == genshin.Game.GENSHIN]
    hk3_accounts = [a for a in accounts if a.game == genshin.Game.HONKAI]
    sr_accounts = [a for a in accounts if a.game == genshin.Game.STARRAIL]

    user = await Database.select_one(User, User.discord_id.is_(user_id))
    if user is None:
        user = User(user_id)

    # 個別遊戲設定 cookie、UID
    character_list: list[str] = []  # 保存角色數量訊息
    user.cookie_default = cookie
    if genshin.Game.GENSHIN in games:
        user.cookie_genshin = cookie
        if len(gs_accounts) == 1:
            user.uid_genshin = gs_accounts[0].uid
        elif len(gs_accounts) > 1:
            character_list.append(f"{len(gs_accounts)}名原神角色")

    if genshin.Game.HONKAI in games:
        user.cookie_honkai3rd = cookie
        if len(hk3_accounts) == 1:
            user.uid_honkai3rd = hk3_accounts[0].uid
        elif len(hk3_accounts) > 1:
            character_list.append(f"{len(hk3_accounts)}名崩壞3角色")

    if genshin.Game.STARRAIL in games:
        user.cookie_starrail = cookie
        if len(sr_accounts) == 1:
            user.uid_starrail = sr_accounts[0].uid
        if len(sr_accounts) > 1:
            character_list.append(f"{len(sr_accounts)}名星穹鐵道角色")

    await Database.insert_or_replace(user)
    LOG.Info(f"{LOG.User(user_id)} Cookie設置成功")

    result = "Cookie已設定完成！"
    # 若有多名角色，則提示使用者要設定 UID
    if len(character_list) > 0:
        result += (
            f"\n你的帳號內共有{'、'.join(character_list)}，"
            + f"請使用 {get_app_command_mention('uid設定')} 指定要保存的角色。"
        )
    return result


@generalErrorHandler
async def get_game_accounts(
    user_id: int, game: genshin.Game
) -> Sequence[genshin.models.GenshinAccount]:
    """取得同一個Hoyolab帳號下，指定遊戲的所有伺服器帳號

    Parameters
    ------
    user_id: `int`
        使用者 Discord ID
    game: `genshin.Game`
        指定遊戲

    Returns
    ------
    `Sequence[GenshinAccount]`
        查詢結果
    """
    client = await get_genshin_client(user_id, game=game, check_uid=False)
    accounts = await client.get_game_accounts()
    return [account for account in accounts if account.game == game]


@generalErrorHandler
async def get_realtime_notes(user_id: int) -> genshin.models.Notes:
    """取得使用者的即時便箋

    Parameters
    ------
    user_id: `int`
        使用者Discord ID

    Returns
    ------
    `Notes`
        查詢結果
    """
    client = await get_genshin_client(user_id)
    return await client.get_genshin_notes(client.uid)


@generalErrorHandler
async def redeem_code(
    user_id: int, client: genshin.Client, code: str, game: genshin.Game = genshin.Game.GENSHIN
) -> str:
    """為使用者使用指定的兌換碼

    Parameters
    ------
    user_id: `int`
        使用者 Discord ID
    client: `genshin.Client`
        genshin.py 的 client
    code: `str`
        Hoyolab 兌換碼
    game: `genshin.Game`
        要兌換的遊戲
    Returns
    ------
    `str`
        回覆給使用者的訊息
    """
    try:
        await client.redeem_code(code, client.uids.get(game), game=game)
    except genshin.errors.GenshinException as e:
        if "兌換碼" in e.original:  # genshin.py 只有對英文的 redemption 做處理
            raise genshin.errors.RedemptionException(
                {"retcode": e.retcode, "message": e.original}, e.msg
            ) from e
        raise
    return "兌換碼使用成功！"


async def claim_daily_reward(
    user_id: int,
    *,
    has_genshin: bool = False,
    has_honkai3rd: bool = False,
    has_starrail: bool = False,
) -> str:
    """為使用者在Hoyolab簽到

    Parameters
    ------
    user_id: `int`
        使用者Discord ID
    has_genshin: `bool`
        是否簽到原神
    honkai3rd: `bool`
        是否簽到崩壞3
    has_starrail: `bool`
        是否簽到星穹鐵道

    Returns
    ------
    `str`
        回覆給使用者的訊息
    """
    try:
        client = await get_genshin_client(user_id, check_uid=False)
    except Exception as e:
        return str(e)

    game_name = {
        genshin.Game.GENSHIN: "原神",
        genshin.Game.HONKAI: "崩壞3",
        genshin.Game.STARRAIL: "星穹鐵道",
    }

    async def claim_reward(game: genshin.Game, retry: int = 5) -> str:
        try:
            reward = await client.claim_daily_reward(game=game)
        except genshin.errors.AlreadyClaimed:
            return f"{game_name[game]}今日獎勵已經領過了！"
        except genshin.errors.InvalidCookies:
            return "Cookie已失效，請從Hoyolab重新取得新Cookie。"
        except genshin.errors.GeetestTriggered:
            link: str = {
                genshin.Game.GENSHIN: "https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481",
                genshin.Game.HONKAI: "https://act.hoyolab.com/bbs/event/signin-bh3/index.html?act_id=e202110291205111",
                genshin.Game.STARRAIL: "https://act.hoyolab.com/bbs/event/signin/hkrpg/index.html?act_id=e202303301540311",
            }.get(game, "")
            return f"{game_name[game]}簽到失敗：受到圖形驗證阻擋，請到 [官網]({link}) 上手動簽到。"
        except Exception as e:
            if isinstance(e, genshin.errors.GenshinException) and e.retcode == -10002:
                return f"{game_name[game]}簽到失敗，目前登入的帳號未查詢到角色資料。"

            LOG.FuncExceptionLog(user_id, "claimDailyReward", e)
            if retry > 0:
                await asyncio.sleep(1)
                return await claim_reward(game, retry - 1)

            LOG.Error(f"{LOG.User(user_id)} {game_name[game]}簽到失敗")
            sentry_sdk.capture_exception(e)
            return f"{game_name[game]}簽到失敗：{e}。"
        else:
            return f"{game_name[game]}今日簽到成功，獲得 {reward.amount}x {reward.name}！"

    if any([has_genshin, has_honkai3rd, has_starrail]) is False:
        return "未選擇任何遊戲簽到"
    result = ""
    if has_genshin:
        result += await claim_reward(genshin.Game.GENSHIN)
    if has_honkai3rd:
        result += await claim_reward(genshin.Game.HONKAI)
    if has_starrail:
        result += await claim_reward(genshin.Game.STARRAIL)

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
async def get_spiral_abyss(user_id: int, previous: bool = False) -> GenshinSpiralAbyss:
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
        return GenshinSpiralAbyss(user_id, abyss.season, abyss, None)
    return GenshinSpiralAbyss(user_id, abyss.season, abyss, characters)


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
    user_id: int,
    *,
    game: genshin.Game = genshin.Game.GENSHIN,
    check_uid=True,
) -> genshin.Client:
    """設定並取得原神 API 的 Client

    Parameters
    ------
    user_id: `int`
        使用者 Discord ID
    game: `genshin.Game`
        要取得的遊戲 Client
    check_uid: `bool`
        是否檢查 UID

    Returns
    ------
    `genshin.Client`
        原神 API 的 Client
    """
    user = await Database.select_one(User, User.discord_id.is_(user_id))
    check, msg = await database.Tool.check_user(user, check_uid=check_uid, game=game)
    if check is False or user is None:
        raise UserDataNotFound(msg)

    match game:
        case genshin.Game.GENSHIN:
            uid = user.uid_genshin or 0
            cookie = user.cookie_genshin or user.cookie_default
        case genshin.Game.HONKAI:
            uid = user.uid_honkai3rd or 0
            cookie = user.cookie_honkai3rd or user.cookie_default
        case genshin.Game.STARRAIL:
            uid = user.uid_starrail or 0
            cookie = user.cookie_starrail or user.cookie_default
        case _:
            uid = 0
            cookie = user.cookie_default

    if str(uid)[0] in ["1", "2", "5"]:
        client = genshin.Client(region=genshin.Region.CHINESE, lang="zh-cn")
    else:
        client = genshin.Client(lang="zh-tw")

    client.set_cookies(cookie)
    client.default_game = game
    client.uid = uid
    return client
