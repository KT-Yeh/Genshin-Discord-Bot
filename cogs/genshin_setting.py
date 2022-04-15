import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from typing import Optional
from utility.GenshinApp import genshin_app

class Setting(commands.Cog, name='設定'):
    def __init__(self, bot):
        self.bot = bot

    # 提交Cookie的表單
    class SubmitCookie(discord.ui.Modal, title='提交Cookie'):
        cookie = discord.ui.TextInput(
            label='Cookie',
            placeholder='請貼上從網頁上取得的Cookie',
            style=discord.TextStyle.long,
            required=True,
            min_length=100,
            max_length=1500
        )
        async def on_submit(self, interaction: discord.Interaction):
            result = await genshin_app.setCookie(str(interaction.user.id), self.cookie.value)
            await interaction.response.send_message(result, ephemeral=True)
        
        async def on_error(self, error: Exception, interaction: discord.Interaction):
            await interaction.response.send_message('發生未知錯誤', ephemeral=True)

    # 設定使用者Cookie
    @app_commands.command(
        name='cookie設定',
        description='設定Cookie，第一次使用前必須先使用本指令設定Cookie')
    @app_commands.rename(option='選項')
    @app_commands.choices(option=[
        Choice(name='說明如何取得Cookie', value=0),
        Choice(name='提交已取得的Cookie', value=1)])
    async def slash_cookie(self, interaction: discord.Interaction, option: int):
        if option == 0:
            help_msg = "1.電腦開啟Hoyolab登入帳號 <https://www.hoyolab.com>\n2.按F12打開開發者工具，切換至主控台(Console)頁面\n3.複製底下程式碼，貼在主控台中按Enter取得Cookie\n4.在這輸入結果，範例：`/cookie設定 提交已取得的Cookie`\n```js\nd=document.cookie; c=d.includes('account_id') || alert('過期或無效的Cookie,請先登出帳號再重新登入!'); c && confirm('將Cookie複製到剪貼簿?') && copy(d)```https://i.imgur.com/dP4RKsb.png"
            await interaction.response.send_message(help_msg)
        elif option == 1:
            await interaction.response.send_modal(self.SubmitCookie())

    # 設定原神UID，當帳號內有多名角色時，保存指定的UID
    @app_commands.command(
        name='uid設定',
        description='帳號內多角色時需保存指定的UID，只有單一角色不需要使用本指令')
    @app_commands.describe(uid='請輸入要保存的原神主要角色UID')
    async def slash_uid(self, interaction: discord.Interaction, uid: int):
        result = await genshin_app.setUID(str(interaction.user.id), str(uid), check_uid=True)
        await interaction.response.send_message(result, ephemeral=True)

    # 清除資料確認按紐
    class Confirm(discord.ui.View):
        def __init__(self, *, timeout: Optional[float] = 60):
            super().__init__(timeout=timeout)
            self.value = None
        
        @discord.ui.button(label='取消', style=discord.ButtonStyle.green)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            self.value = False
            self.stop()
        
        @discord.ui.button(label='確定', style=discord.ButtonStyle.red)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            self.value = True
            self.stop()
    
    # 刪除已保存的個人資料
    @app_commands.command(
        name='清除資料',
        description='刪除使用者所有保存在小幫手內的個人資料')
    async def slash_clear(self, interaction: discord.Interaction):
        view = self.Confirm()
        await interaction.response.send_message('是否確定刪除？', view=view, ephemeral=True)
        
        await view.wait()
        if view.value == True:
            result = genshin_app.clearUserData(str(interaction.user.id))
            await interaction.edit_original_message(content=result, view=None)
        else:
            await interaction.edit_original_message(content='取消指令', view=None)

async def setup(client: commands.Bot):
    await client.add_cog(Setting(client))