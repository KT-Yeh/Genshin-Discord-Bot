from typing import Literal, Optional

import discord
import genshin
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from utility import EmbedTemplate, config, custom_log

from .ui_genshin import SpiralAbyssUI
from .ui_starrail import ChooseAbyssModeButton, ForgottenHallUI


class SpiralAbyssCog(commands.Cog, name="深境螺旋"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="abyss深淵紀錄", description="查詢深境螺旋紀錄")
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
    @app_commands.rename(game="遊戲", season="時間", user="使用者")
    @app_commands.describe(season="選擇本期、上期或是歷史紀錄", user="查詢其他成員的資料，不填寫則查詢自己")
    @app_commands.choices(
        game=[
            Choice(name="原神", value="genshin"),
            Choice(name="星穹鐵道", value="hkrpg"),
        ],
        season=[
            Choice(name="本期紀錄", value="THIS_SEASON"),
            Choice(name="上期紀錄", value="PREVIOUS_SEASON"),
            Choice(name="歷史紀錄", value="HISTORICAL_RECORD"),
        ],
    )
    @custom_log.SlashCommandLogger
    async def slash_abyss(
        self,
        interaction: discord.Interaction,
        game: genshin.Game,
        season: Literal["THIS_SEASON", "PREVIOUS_SEASON", "HISTORICAL_RECORD"],
        user: Optional[discord.User] = None,
    ):
        match game:
            case genshin.Game.GENSHIN:
                await SpiralAbyssUI.abyss(interaction, user or interaction.user, season)
            case genshin.Game.STARRAIL:
                # 選擇忘卻之庭、虛構敘事
                view = ChooseAbyssModeButton()
                await interaction.response.send_message(view=view)
                await view.wait()

                if view.value is None:
                    return
                mode = view.value
                await ForgottenHallUI.launch(interaction, user or interaction.user, mode, season)
            case _:
                return

    @slash_abyss.error
    async def on_slash_abyss_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                embed=EmbedTemplate.error(f"使用指令的間隔為{config.slash_cmd_cooldown}秒，請稍後再使用~"),
                ephemeral=True,
            )


async def setup(client: commands.Bot):
    await client.add_cog(SpiralAbyssCog(client))

    # -------------------------------------------------------------
    # 下面為Context Menu指令
    @client.tree.context_menu(name="深淵紀錄(上期)")
    @custom_log.ContextCommandLogger
    async def context_abyss_previous(interaction: discord.Interaction, user: discord.User):
        await SpiralAbyssUI.abyss(interaction, user, "PREVIOUS_SEASON")

    @client.tree.context_menu(name="深淵紀錄(本期)")
    @custom_log.ContextCommandLogger
    async def context_abyss(interaction: discord.Interaction, user: discord.User):
        await SpiralAbyssUI.abyss(interaction, user, "THIS_SEASON")
