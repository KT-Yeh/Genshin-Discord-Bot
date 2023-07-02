import asyncio

import discord
import genshin
from discord import app_commands
from discord.ext import commands

import genshin_py
from utility import EmbedTemplate
from utility.custom_log import SlashCommandLogger

from .ui import DropdownView


class CharactersCog(commands.Cog, name="角色一覽"):
    """斜線指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="character角色一覽", description="公開展示我的所有角色")
    @app_commands.rename(game="遊戲")
    @app_commands.choices(
        game=[
            app_commands.Choice(name="原神", value="genshin"),
            app_commands.Choice(name="星穹鐵道", value="hkrpg"),
        ],
    )
    @SlashCommandLogger
    async def slash_characters(self, interaction: discord.Interaction, game: genshin.Game):
        try:
            match game:
                case genshin.Game.GENSHIN:
                    defer, characters = await asyncio.gather(
                        interaction.response.defer(),
                        genshin_py.get_genshin_characters(interaction.user.id),
                    )
                case genshin.Game.STARRAIL:
                    defer, characters = await asyncio.gather(
                        interaction.response.defer(),
                        genshin_py.get_starrail_characters(interaction.user.id),
                    )
                case _:
                    return
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            view = DropdownView(interaction.user, characters)
            await interaction.edit_original_response(content="請選擇角色：", view=view)


async def setup(client: commands.Bot):
    await client.add_cog(CharactersCog(client))
