import asyncio
from typing import Literal, Optional, Union

import discord
import sentry_sdk
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import genshin_py
from utility import EmbedTemplate, config
from utility.custom_log import LOG, ContextCommandLogger, SlashCommandLogger


class RecordCard:
    """遊戲紀錄卡片"""

    @staticmethod
    async def card(
        interaction: discord.Interaction,
        user: Union[discord.User, discord.Member],
        option: Literal["RECORD", "EXPLORATION"],
    ):
        try:
            defer, (uid, userstats) = await asyncio.gather(
                interaction.response.defer(), genshin_py.get_genshin_record_card(user.id)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
            return

        try:
            avatar_bytes = await user.display_avatar.read()
            if option == "RECORD":
                fp = genshin_py.draw_record_card(avatar_bytes, uid, userstats)
            elif option == "EXPLORATION":
                fp = genshin_py.draw_exploration_card(avatar_bytes, uid, userstats)
        except Exception as e:
            LOG.ErrorLog(interaction, e)
            sentry_sdk.capture_exception(e)
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            fp.seek(0)
            await interaction.edit_original_response(
                attachments=[discord.File(fp=fp, filename="image.jpeg")]
            )
            fp.close()


class RecordCardCog(commands.Cog, name="紀錄卡片"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="card紀錄卡片", description="產生原神個人遊戲紀錄卡片")
    @app_commands.rename(option="選項", user="使用者")
    @app_commands.describe(option="選擇要查詢數據總覽或是世界探索度", user="查詢其他成員的資料，不填寫則查詢自己")
    @app_commands.choices(
        option=[
            Choice(name="數據總覽", value="RECORD"),
            Choice(name="世界探索", value="EXPLORATION"),
        ]
    )
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
    @SlashCommandLogger
    async def slash_card(
        self,
        interaction: discord.Interaction,
        option: Literal["RECORD", "EXPLORATION"],
        user: Optional[discord.User] = None,
    ):
        await RecordCard.card(interaction, user or interaction.user, option)

    @slash_card.error
    async def on_slash_card_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                embed=EmbedTemplate.error(f"產生卡片的間隔為{config.slash_cmd_cooldown}秒，請稍後再使用~"),
                ephemeral=True,
            )


async def setup(client: commands.Bot):
    await client.add_cog(RecordCardCog(client))

    @client.tree.context_menu(name="遊戲紀錄卡片")
    @ContextCommandLogger
    async def context_card(interaction: discord.Interaction, user: discord.User):
        await RecordCard.card(interaction, user, "RECORD")
