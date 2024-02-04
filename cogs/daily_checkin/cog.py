import asyncio
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import genshin_py
from utility import EmbedTemplate, custom_log


class DailyCheckinCog(commands.Cog, name="每日簽到"):
    """斜線指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="daily每日簽到", description="領取Hoyolab每日簽到獎勵")
    @app_commands.rename(game="遊戲", is_geetest="設定圖形驗證", user="使用者")
    @app_commands.choices(
        game=[
            Choice(name="原神", value="原神"),
            Choice(name="崩壞3", value="崩壞3"),
            Choice(name="星穹鐵道", value="星穹鐵道"),
            Choice(name="未定事件簿(台服)", value="未定事件簿(台服)"),
            Choice(name="未定事件簿(國際服)", value="未定事件簿(國際服)"),
        ]
    )
    @app_commands.choices(
        is_geetest=[
            Choice(name="是", value="是"),
            Choice(name="否", value="否"),
        ]
    )
    @custom_log.SlashCommandLogger
    async def slash_daily(
        self,
        interaction: discord.Interaction,
        game: Literal["原神", "崩壞3", "星穹鐵道", "未定事件簿(台服)", "未定事件簿(國際服)"],
        is_geetest: Literal["是", "否"] = "否",
        user: Optional[discord.User] = None,
    ):
        choice = {
            "has_genshin": True if game == "原神" else False,
            "has_honkai3rd": True if game == "崩壞3" else False,
            "has_starrail": True if game == "星穹鐵道" else False,
            "has_themis": True if game == "未定事件簿(國際服)" else False,
            "has_themis_tw": True if game == "未定事件簿(台服)" else False,
            "is_geetest": True if is_geetest == "是" else False,
        }

        _user = user or interaction.user
        if _user.id == self.bot.application_id:
            _user = interaction.user

        defer, result = await asyncio.gather(
            interaction.response.defer(ephemeral=(is_geetest == "是")),
            genshin_py.claim_daily_reward(_user.id, **choice),
        )
        await interaction.edit_original_response(embed=EmbedTemplate.normal(result))


async def setup(client: commands.Bot):
    await client.add_cog(DailyCheckinCog(client))
