import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from typing import Optional
from utility.GenshinApp import genshin_app

class Setting(commands.Cog, name='設定'):
    def __init__(self, bot):
        self.bot = bot

    # 設定使用者Cookie
    @app_commands.command(
        name='cookie設定', 
        description='設定Cookie，第一次使用前必須先使用本指令設定Cookie')
    @app_commands.describe(cookie='請輸入從網頁上取得的Cookie')
    async def slash_cookie(self, interaction: discord.Interaction, cookie: Optional[str] = None):
        if cookie is None:
            help_msg = "1.電腦開啟Hoyolab登入帳號 <https://www.hoyolab.com>\n2.按F12打開開發者工具，切換至主控台(Console)頁面\n3.複製底下程式碼，貼在主控台中按Enter取得Cookie\n4.在這輸入結果，範例：`/cookie設定 XXXXX(從網頁取得的Cookie)`\n```js\nd=document.cookie; c=d.includes('account_id') || alert('過期或無效的Cookie,請先登出帳號再重新登入!'); c && confirm('將Cookie複製到剪貼簿?') && copy(d)```https://i.imgur.com/dP4RKsb.png"
            await interaction.response.send_message(help_msg)
        else:
            result = await genshin_app.setCookie(str(interaction.user.id), cookie)
            if result.startswith('無效的Cookie'):
                await interaction.response.send_message('無效的Cookie，請重新輸入(使用 `/cookie` 查看教學)', ephemeral=True)
            else:
                await interaction.response.send_message(result, ephemeral=True)

    # 設定原神UID，當帳號內有多名角色時，保存指定的UID
    @app_commands.command(
        name='uid設定',
        description='帳號內多角色時需保存指定的UID，只有單一角色不需要使用本指令')
    @app_commands.describe(uid='請輸入原神角色的UID')
    async def slash_uid(self, interaction: discord.Interaction, uid: int):
        result = genshin_app.setUID(str(interaction.user.id), str(uid))
        await interaction.response.send_message(result)

    # 刪除已保存的個人資料
    @app_commands.command(
        name='清除資料',
        description='刪除使用者所有保存在小幫手內的個人資料')
    @app_commands.rename(confirm='確認刪除')
    @app_commands.describe(confirm='確認刪除保存的資料？')
    @app_commands.choices(confirm=[Choice(name='確認', value=1), Choice(name='取消', value=0)])
    async def slash_clear(self, interaction: discord.Interaction, confirm: int):
        if confirm:
            result = genshin_app.clearUserData(str(interaction.user.id))
            await interaction.response.send_message(result)
        else:
            await interaction.response.send_message('取消指令')

async def setup(client: commands.Bot):
    await client.add_cog(Setting(client))