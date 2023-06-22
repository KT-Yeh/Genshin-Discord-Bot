import asyncio

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from genshin_py import genshin_app, parser
from utility import EmbedTemplate
from utility.custom_log import ContextCommandLogger, SlashCommandLogger


class RealtimeNotes:
    """即時便箋"""

    @staticmethod
    async def notes(
        interaction: discord.Interaction,
        user: discord.User | discord.Member,
        *,
        shortForm: bool = False,
    ):
        try:
            defer, notes = await asyncio.gather(
                interaction.response.defer(), genshin_app.get_realtime_notes(user.id)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            embed = await parser.parse_realtime_notes(notes, user=user, shortForm=shortForm)
            await interaction.edit_original_response(embed=embed)


class RealtimeNotesCog(commands.Cog, name="即時便箋"):
    """取得使用者即時便箋資訊(樹脂、洞天寶錢、派遣...等)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="notes即時便箋", description="查詢即時便箋，包含樹脂、洞天寶錢、探索派遣...等")
    @app_commands.rename(shortForm="顯示格式", user="使用者")
    @app_commands.describe(shortForm="選擇顯示完整或簡約格式(省略每日、週本、探索派遣)", user="查詢其他成員的資料，不填寫則查詢自己")
    @app_commands.choices(shortForm=[Choice(name="完整", value=0), Choice(name="簡約", value=1)])
    @SlashCommandLogger
    async def slash_notes(
        self,
        interaction: discord.Interaction,
        shortForm: int = 0,
        user: discord.User | None = None,
    ):
        await RealtimeNotes.notes(interaction, user or interaction.user, shortForm=bool(shortForm))


async def setup(client: commands.Bot):
    await client.add_cog(RealtimeNotesCog(client))

    @client.tree.context_menu(name="即時便箋")
    @ContextCommandLogger
    async def context_notes(interaction: discord.Interaction, user: discord.User):
        await RealtimeNotes.notes(interaction, user)
