from typing import Literal, Optional

import discord
import enkanetwork
from discord import app_commands
from discord.ext import commands

from utility.custom_log import ContextCommandLogger, SlashCommandLogger

from .ui_genshin import showcase as genshin_showcase
from .ui_starrail import showcase as starrail_showcase


class ShowcaseCog(commands.Cog, name="原神展示櫃"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="showcase角色展示櫃", description="查詢指定UID玩家的公開角色展示櫃")
    @app_commands.rename(game="遊戲", user="使用者")
    @app_commands.describe(uid="欲查詢的玩家UID，若小幫手已保存資料的話查自己不需要填本欄位", user="查詢其他成員的資料，不填寫則查詢自己")
    @app_commands.choices(
        game=[
            app_commands.Choice(name="原神", value="原神"),
            app_commands.Choice(name="星穹鐵道", value="星穹鐵道"),
        ]
    )
    @SlashCommandLogger
    async def slash_showcase(
        self,
        interaction: discord.Interaction,
        game: Literal["原神", "星穹鐵道"],
        uid: Optional[int] = None,
        user: Optional[discord.User] = None,
    ):
        match game:
            case "原神":
                await genshin_showcase(interaction, user or interaction.user, uid)
            case "星穹鐵道":
                await starrail_showcase(interaction, user or interaction.user, uid)


async def setup(client: commands.Bot):
    # 更新 Enka 素材資料
    enka = enkanetwork.EnkaNetworkAPI()
    async with enka:
        await enka.update_assets()
    enkanetwork.Assets(lang=enkanetwork.Language.CHT)

    await client.add_cog(ShowcaseCog(client))

    @client.tree.context_menu(name="角色展示櫃")
    @ContextCommandLogger
    async def context_showcase(interaction: discord.Interaction, user: discord.User):
        await genshin_showcase(interaction, user, None)
