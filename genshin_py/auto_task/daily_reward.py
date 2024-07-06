import asyncio
from datetime import datetime
from typing import Any, ClassVar, Final

import aiohttp
import discord
import sentry_sdk
from discord.ext import commands

import database
from database import Database, GeetestChallenge, ScheduleDailyCheckin, User
from utility import LOG, EmbedTemplate, config

from .. import claim_daily_reward


class DailyReward:
    """自動排程的類別

    Methods
    -----
    execute(bot: `commands.Bot`)
        執行自動排程
    """

    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    # 統計簽到人數
    _total: ClassVar[dict[str, int]] = {}
    """簽到的總人數 dict[host, count]"""
    _honkai_count: ClassVar[dict[str, int]] = {}
    """簽到崩壞3的人數 dict[host, count]"""
    _starrail_count: ClassVar[dict[str, int]] = {}
    """簽到星穹鐵道的人數 dict[host, count]"""
    _zzz_count: ClassVar[dict[str, int]] = {}
    """簽到絕區零的人數 dict[host, count]"""
    _themis_count: ClassVar[dict[str, int]] = {}
    """簽到未定事件簿的人數 dict[host, count]"""

    @classmethod
    async def execute(cls, bot: commands.Bot):
        """執行自動排程，簽到使用者並統計簽到數據

        Parameters
        -----
        bot: `commands.Bot`
            Discord 機器人客戶端
        """
        if cls._lock.locked():
            return
        await cls._lock.acquire()
        try:
            LOG.System("每日自動簽到開始")

            # 初始化
            queue: asyncio.Queue[ScheduleDailyCheckin] = asyncio.Queue()
            cls._total = {}
            cls._honkai_count = {}
            cls._starrail_count = {}
            cls._zzz_count = {}
            cls._themis_count = {}
            daily_users = await Database.select_all(ScheduleDailyCheckin)

            # 將所有需要簽到的使用者放入佇列 (Producer)
            for user in daily_users:
                if user.next_checkin_time < datetime.now():
                    await queue.put(user)

            # 建立本地簽到任務 (Consumer)
            tasks = [asyncio.create_task(cls._claim_daily_reward_task(queue, "LOCAL", bot))]
            # 建立遠端簽到任務 (Consumer)
            for host in config.daily_reward_api_list:
                tasks.append(asyncio.create_task(cls._claim_daily_reward_task(queue, host, bot)))

            await queue.join()  # 等待所有使用者簽到完成
            for task in tasks:  # 關閉簽到任務
                task.cancel()

            _log_message = (
                f"自動簽到結束：總共 {sum(cls._total.values())} 人簽到，"
                + f"其中 {sum(cls._honkai_count.values())} 人簽到崩壞3、"
                + f"{sum(cls._starrail_count.values())} 人簽到星穹鐵道、"
                + f"{sum(cls._zzz_count.values())} 人簽到絕區零、"
                + f"{sum(cls._themis_count.values())} 人簽到未定事件簿\n"
            )
            for host in cls._total.keys():
                _log_message += (
                    f"- {host}：{cls._total.get(host)}、{cls._honkai_count.get(host)}、"
                    + f"{cls._starrail_count.get(host)}、{cls._zzz_count.get(host)}\n"
                )
            LOG.System(_log_message)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            LOG.Error(f"自動排程 DailyReward 發生錯誤：{e}")
        finally:
            cls._lock.release()

    @classmethod
    async def _claim_daily_reward_task(
        cls, queue: asyncio.Queue[ScheduleDailyCheckin], host: str, bot: commands.Bot
    ):
        """從傳入的 asyncio.Queue 裡面取得使用者，然後進行每日簽到，並根據簽到結果發送訊息給使用者

        Parameters
        -----
        queue: `asyncio.Queue[ScheduleDailyCheckin]`
            存放需要簽到的使用者的佇列
        host: `str`
            簽到的主機
            - 本地：固定為字串 "LOCAL"
            - 遠端：簽到 API 網址

        bot: `commands.Bot`
            Discord 機器人客戶端
        """
        LOG.Info(f"自動排程簽到任務開始：{host}")
        if host != "LOCAL":
            # 先測試 API 是否正常
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(host) as resp:
                        if resp.status != 200:
                            raise Exception(f"Http 狀態碼 {resp.status}")
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    LOG.Error(f"自動排程 DailyReward 測試 API {host} 時發生錯誤：{e}")
                    return

        cls._total[host] = 0  # 初始化簽到人數
        cls._honkai_count[host] = 0  # 初始化簽到崩壞3的人數
        cls._starrail_count[host] = 0  # 初始化簽到星穹鐵道的人數
        cls._zzz_count[host] = 0  # 初始化簽到絕區零的人數
        cls._themis_count[host] = 0  # 初始化簽到未定事件簿的人數
        MAX_API_ERROR_COUNT: Final[int] = 20  # 遠端 API 發生錯誤的最大次數
        api_error_count = 0  # 遠端 API 發生錯誤的次數

        while True:
            user = await queue.get()
            try:
                message = await cls._claim_daily_reward(host, user)
            except Exception as e:
                await queue.put(user)  # 簽到發生異常，將使用者放回佇列
                api_error_count += 1
                LOG.Error(f"遠端 API：{host} 發生錯誤 ({api_error_count}/{MAX_API_ERROR_COUNT})")
                # 如果發生錯誤超過 MAX_API_ERROR_COUNT 次，則停止簽到任務
                if api_error_count >= MAX_API_ERROR_COUNT:
                    sentry_sdk.capture_exception(e)
                    return
            else:
                # 簽到成功後，更新資料庫中的簽到日期、發送訊息給使用者、更新計數器
                user.update_next_checkin_time()
                await Database.insert_or_replace(user)
                if message is not None:
                    await cls._send_message(bot, user, message)
                    cls._total[host] += 1
                    cls._honkai_count[host] += int(user.has_honkai3rd)
                    cls._starrail_count[host] += int(user.has_starrail)
                    cls._zzz_count[host] += int(user.has_zzz)
                    cls._themis_count[host] += int(user.has_themis) + int(user.has_themis_tw)
                    await asyncio.sleep(config.schedule_loop_delay)
            finally:
                queue.task_done()

    @classmethod
    async def _claim_daily_reward(cls, host: str, user: ScheduleDailyCheckin) -> str | None:
        """
        為使用者進行每日簽到。

        Parameters
        ----------
        host: `str`
            簽到的主機
            - 本地：固定為字串 "LOCAL"
            - 遠端：簽到 API 網址
        user: `ScheduleDailyCheckin`
            需要簽到的使用者

        Returns
        -------
        str | None
            簽到結果訊息； None 表示跳過此使用者。

        Raises
        ------
        Exception
            如果簽到失敗，會拋出一個 Exception。
        """
        if host == "LOCAL":  # 本地簽到
            message = await claim_daily_reward(
                user.discord_id,
                has_genshin=user.has_genshin,
                has_honkai3rd=user.has_honkai3rd,
                has_starrail=user.has_starrail,
                has_zzz=user.has_zzz,
                has_themis=user.has_themis,
                has_themis_tw=user.has_themis_tw,
            )
            return message
        else:  # 遠端 API 簽到
            # 為了有 cookie，所以這裡從資料庫取得 User Table 的資料
            user_data = await Database.select_one(User, User.discord_id.is_(user.discord_id))
            gt_challenge = await Database.select_one(
                GeetestChallenge, GeetestChallenge.discord_id.is_(user.discord_id)
            )
            if user_data is None:
                return None
            check, msg = await database.Tool.check_user(user_data)
            if check is False:
                return msg
            payload: dict[str, Any] = {
                "discord_id": user.discord_id,
                "uid": 0,
                "cookie": user_data.cookie_default,
                "cookie_genshin": user_data.cookie_genshin,
                "cookie_honkai3rd": user_data.cookie_honkai3rd,
                "cookie_starrail": user_data.cookie_starrail,
                "cookie_zzz": user_data.cookie_zzz,
                "cookie_themis": user_data.cookie_themis,
                "has_genshin": "true" if user.has_genshin else "false",
                "has_honkai": "true" if user.has_honkai3rd else "false",
                "has_starrail": "true" if user.has_starrail else "false",
                "has_zzz": "true" if user.has_zzz else "false",
                "has_themis": "true" if user.has_themis else "false",
                "has_themis_tw": "true" if user.has_themis_tw else "false",
            }
            if gt_challenge is not None:
                payload.update(
                    {
                        "geetest_genshin": gt_challenge.genshin,
                        "geetest_honkai3rd": gt_challenge.honkai3rd,
                        "geetest_starrail": gt_challenge.starrail,
                    }
                )
            async with aiohttp.ClientSession() as session:
                async with session.post(url=host + "/daily-reward", json=payload) as resp:
                    if resp.status == 200:
                        result: dict[str, str] = await resp.json()
                        message = result.get("message", "遠端 API 簽到失敗")
                        return message
                    else:
                        raise Exception(f"{host} 簽到失敗，HTTP 狀態碼：{resp.status}")

    @classmethod
    async def _send_message(cls, bot: commands.Bot, user: ScheduleDailyCheckin, message: str):
        """向使用者發送簽到結果的訊息"""
        try:
            _id = user.discord_channel_id
            channel = bot.get_channel(_id) or await bot.fetch_channel(_id)
            # 若不用@提及使用者，則先取得此使用者的名稱然後發送訊息
            if user.is_mention is False and "Cookie已失效" not in message:
                _user = await bot.fetch_user(user.discord_id)
                await channel.send(embed=EmbedTemplate.normal(f"[自動簽到] {_user.name}：{message}"))  # type: ignore
            else:  # 若需要@提及使用者或是 Cookie 已失效
                await channel.send(f"<@{user.discord_id}>", embed=EmbedTemplate.normal(f"[自動簽到] {message}"))  # type: ignore
        except (
            discord.Forbidden,
            discord.NotFound,
            discord.InvalidData,
        ) as e:  # 發送訊息失敗，移除此使用者
            LOG.Except(f"自動簽到發送訊息失敗，移除此使用者 {LOG.User(user.discord_id)}：{e}")
            await Database.delete_instance(user)
        except Exception as e:
            sentry_sdk.capture_exception(e)
