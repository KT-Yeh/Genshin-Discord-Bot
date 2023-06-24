import asyncio

import discord
import genshin
from discord import app_commands
from discord.ext import commands

import genshin_py
from utility import EmbedTemplate
from utility.custom_log import SlashCommandLogger

from .ui import Dropdown, View


class NoticesCog(commands.Cog, name="遊戲公告"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="notices原神公告", description="顯示原神的遊戲公告與活動公告")
    @SlashCommandLogger
    async def slash_notices(self, interaction: discord.Interaction):
        try:
            defer, notices = await asyncio.gather(
                interaction.response.defer(), genshin_py.get_genshin_notices()
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            # 將公告分成活動公告、遊戲公告、祈願公告三類
            game: list[genshin.models.Announcement] = []
            event: list[genshin.models.Announcement] = []
            wish: list[genshin.models.Announcement] = []
            for notice in notices:
                if notice.type == 1:
                    if "祈願" in notice.subtitle:
                        wish.append(notice)
                    else:
                        event.append(notice)
                elif notice.type == 2:
                    game.append(notice)

            view = View()
            if len(game) > 0:
                view.add_item(Dropdown(game, "遊戲公告："))
            if len(event) > 0:
                view.add_item(Dropdown(event, "活動公告："))
            if len(wish) > 0:
                view.add_item(Dropdown(wish, "祈願卡池："))
            await interaction.edit_original_response(view=view)


async def setup(client: commands.Bot):
    await client.add_cog(NoticesCog(client))
