import discord
from discord import app_commands
from discord.ext import commands

from database import Database
from utility import custom_log

from .ui import ConfirmButton


class ClearSettingCog(commands.Cog, name="清除設定"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="清除資料", description="刪除使用者所有保存在小幫手內的個人資料")
    @custom_log.SlashCommandLogger
    async def slash_clear(self, interaction: discord.Interaction):
        view = ConfirmButton()
        await interaction.response.send_message("是否確定刪除？", view=view, ephemeral=True)

        await view.wait()
        if view.value is True:
            await Database.delete_all(interaction.user.id)
            await interaction.edit_original_response(content="使用者資料已全部刪除", view=None)
        else:
            await interaction.edit_original_response(content="取消指令", view=None)


async def setup(client: commands.Bot):
    await client.add_cog(ClearSettingCog(client))
