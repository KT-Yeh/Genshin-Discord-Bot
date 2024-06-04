import asyncio
import datetime
from typing import Callable

import aiohttp
import genshin
import sentry_sdk

from database import Database, User
from utility import LOG, config

from .errors import GenshinAPIException, UserDataNotFound


def generalErrorHandler(func: Callable):
    """對於使用genshin.py函式的通用例外處理裝飾器"""

    async def wrapper(*args, **kwargs):
        user_id = -1
        # 從函式參數找出 user_id
        for arg in args:
            if isinstance(arg, int) and len(str(arg)) >= 15:
                user_id = arg
                break
        try:
            # 針對特定錯誤加入重試機制
            RETRY_MAX = 3
            for retry in range(RETRY_MAX, -1, -1):
                try:
                    result = await func(*args, **kwargs)

                    # 成功使用指令則更新使用者的最後使用時間
                    user = await Database.select_one(User, User.discord_id.is_(user_id))
                    if user is not None:
                        user.last_used_time = datetime.datetime.now()
                        await Database.insert_or_replace(user)

                    return result
                except (genshin.errors.InternalDatabaseError, aiohttp.ClientOSError) as e:
                    LOG.FuncExceptionLog(user_id, f"{func.__name__} (retry={retry})", e)
                    if retry == 0:  # 當重試次數用完時拋出例外
                        raise
                    else:
                        # 重試之間加入等待時間，並遞增每次的等待時間
                        await asyncio.sleep(1.0 + RETRY_MAX - retry)
                        continue
        except genshin.errors.DataNotPublic as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            raise GenshinAPIException(e, "此功能權限未開啟，請先從Hoyolab網頁或App上的個人戰績->設定，將此功能啟用")
        except genshin.errors.InvalidCookies as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            raise GenshinAPIException(e, "Cookie已失效，請從Hoyolab重新取得新Cookie")
        except genshin.errors.GeetestError as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            url = f"{config.geetest_solver_url}/geetest/starrail_battlechronicle/{user_id}"
            raise GenshinAPIException(e, f"觸發 Hoyolab 圖形驗證，請 [>>點擊此連結<<]({url}/) 到網頁上進行手動解鎖。")
        except genshin.errors.RedemptionException as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            raise GenshinAPIException(e, e.original)
        except genshin.errors.GenshinException as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            sentry_sdk.capture_exception(e)
            raise GenshinAPIException(e, e.original)
        except UserDataNotFound as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            raise Exception(str(e))
        except Exception as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            sentry_sdk.capture_exception(e)
            raise

    return wrapper
