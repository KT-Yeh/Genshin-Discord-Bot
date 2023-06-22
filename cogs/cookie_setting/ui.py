import discord

from genshin_py import genshin_app
from utility import EmbedTemplate


class CookieModal(discord.ui.Modal, title="提交Cookie"):
    """提交Cookie的表單"""

    cookie: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Cookie",
        placeholder='請貼上從網頁上取得的Cookie，取得方式請使用指令 "/cookie設定 顯示說明如何取得Cookie"',
        style=discord.TextStyle.long,
        required=True,
        min_length=50,
        max_length=2000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=EmbedTemplate.normal("設定中，請稍後..."), ephemeral=True
        )
        try:
            msg = await genshin_app.set_cookie(interaction.user.id, self.cookie.value)
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            await interaction.edit_original_response(embed=EmbedTemplate.normal(msg))
