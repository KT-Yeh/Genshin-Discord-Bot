import discord

from utility import config


class ConfirmButton(discord.ui.View):
    """清除資料確認按紐"""

    def __init__(self):
        super().__init__(timeout=config.discord_view_short_timeout)
        self.value = None

    @discord.ui.button(label="取消", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = False
        self.stop()

    @discord.ui.button(label="確定", style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = True
        self.stop()
