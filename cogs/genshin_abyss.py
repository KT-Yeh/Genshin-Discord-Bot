import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from typing import Literal
from utility.GenshinApp import genshin_app
from utility.draw import drawAbyssCard
from utility.utils import EmbedTemplate
from utility.config import config
from utility import CustomLog
from data.database import SpiralAbyssData

class SpiralAbyss:
    """深境螺旋"""
    class AuthorOnlyView(discord.ui.View):
        """只有原本Interaction使用者才能使用的View"""
        def __init__(self, author: discord.User):
            self.author = author
            super().__init__(timeout=config.discord_view_short_timeout)
        
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id != self.author.id:
                await interaction.response.send_message(embed=EmbedTemplate.error('指令呼叫者才能進行操作'), ephemeral=True)
                return False
            return True

    class AbyssFloorDropdown(discord.ui.Select):
        """選擇深淵樓層的下拉選單"""
        def __init__(self, overview: discord.Embed, abyss_data: SpiralAbyssData):
            options = [discord.SelectOption(
                    label=f"[★{floor.stars}] 第 {floor.floor} 層",
                    description=genshin_app.parseAbyssChamber(floor.chambers[-1]),
                    value=str(i)
                ) for i, floor in enumerate(abyss_data.abyss.floors)
            ]
            super().__init__(placeholder='選擇樓層：', options=options)
            self.embed = overview
            self.abyss_data = abyss_data
        
        async def callback(self, interaction: discord.Interaction):
            fp = drawAbyssCard(self.abyss_data.abyss.floors[int(self.values[0])], self.abyss_data.characters)
            fp.seek(0)
            self.embed.set_image(url="attachment://image.jpeg")
            await interaction.response.edit_message(embed=self.embed, attachments=[discord.File(fp, "image.jpeg")])
    
    @staticmethod
    async def presentation(interaction: discord.Interaction, user: discord.User, abyss_data: SpiralAbyssData, *, view_item: discord.ui.Item = None):
        embed = genshin_app.parseAbyssOverview(abyss_data.abyss)
        embed.title = f'{user.display_name} 的深境螺旋戰績'
        embed.set_thumbnail(url=user.display_avatar.url)
        view = None
        if len(abyss_data.abyss.floors) > 0:
            view = SpiralAbyss.AuthorOnlyView(interaction.user)
            if view_item:
                view.add_item(SpiralAbyss.AbyssFloorDropdown(embed, abyss_data))
                view.add_item(view_item)
            else:
                view.add_item(SpiralAbyss.AbyssFloorDropdown(embed, abyss_data))
        await interaction.edit_original_response(embed=embed, view=view, attachments=[])
    
    @staticmethod
    async def abyss(interaction: discord.Interaction, user: discord.User, season_choice: Literal[0, 1]):
        try:
            defer, abyss_data = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.getSpiralAbyss(user.id, bool(season_choice)),
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(str(e)))
        else:
            await SpiralAbyss.presentation(interaction, user, abyss_data)

class SpiralAbyssCog(commands.Cog, name='深境螺旋'):
    """斜線指令"""
    def __init__(self, bot):
        self.bot = bot

    #-------------------------------------------------------------
    # 取得深境螺旋資訊
    @app_commands.command(
        name='abyss深淵紀錄',
        description='查詢深境螺旋紀錄')
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
    @app_commands.rename(season='時間', user='使用者')
    @app_commands.describe(
        season='選擇本期或是上期紀錄',
        user='查詢其他成員的資料，不填寫則查詢自己')
    @app_commands.choices(
        season=[Choice(name='本期紀錄', value=0),
                Choice(name='上期紀錄', value=1)])
    @CustomLog.SlashCommandLogger
    async def slash_abyss(self, interaction: discord.Interaction, season: int, user: discord.User = None):
        await SpiralAbyss.abyss(interaction, user or interaction.user, season)

    @slash_abyss.error
    async def on_slash_abyss_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(embed=EmbedTemplate.error(f'使用指令的間隔為{config.slash_cmd_cooldown}秒，請稍後再使用~'), ephemeral=True)

async def setup(client: commands.Bot):
    await client.add_cog(SpiralAbyssCog(client))

    #-------------------------------------------------------------
    # 下面為Context Menu指令
    @client.tree.context_menu(name='深淵紀錄(上期)')
    @CustomLog.ContextCommandLogger
    async def context_abyss_previous(interaction: discord.Interaction, user: discord.User):
        await SpiralAbyss.abyss(interaction, user, 1)

    @client.tree.context_menu(name='深淵紀錄(本期)')
    @CustomLog.ContextCommandLogger
    async def context_abyss(interaction: discord.Interaction, user: discord.User):
        await SpiralAbyss.abyss(interaction, user, 0)
