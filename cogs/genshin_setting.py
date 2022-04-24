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
    class CookieModal(discord.ui.Modal, title='提交Cookie'):
        cookie = discord.ui.TextInput(
            label='Cookie',
            placeholder='請貼上從網頁上取得的Cookie，取得方式請使用指令 "/cookie設定 顯示說明如何取得Cookie"',
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
        Choice(name='① 顯示說明如何取得Cookie', value=0),
        Choice(name='② 提交已取得的Cookie給小幫手', value=1),
        Choice(name='③ 顯示小幫手Cookie使用與保存告知', value=2)])
    async def slash_cookie(self, interaction: discord.Interaction, option: int):
        if option == 0:
            help_msg = (
            "1.先複製本文最底下整段程式碼\n"
            "2.PC或手機使用Chrome開啟Hoyolab登入帳號 <https://www.hoyolab.com>\n"
            "3.在網址列先輸入 `java`，然後貼上程式碼，確保網址開頭變成 `javascript:`\n"
            "4.按Enter，網頁會變成顯示你的Cookie，全選然後複製\n"
            "5.在這裡提交結果，使用：`/cookie設定 提交已取得的Cookie`\n"
            "· 遇到問題嗎？點連結看其他方法：<https://bit.ly/3LgQkg0>\n"
            "https://i.imgur.com/OQ8arx0.gif")
            code_msg = "```script:d=document.cookie; c=d.includes('account_id') || alert('過期或無效的Cookie,請先登出帳號再重新登入!'); c && document.write(d)```"
            await interaction.response.send_message(content=help_msg)
            await interaction.followup.send(content=code_msg)
        elif option == 1:
            await interaction.response.send_modal(self.CookieModal())
        elif option == 2:
            msg = ('· Cookie的內容包含你個人的識別代碼，不包含帳號與密碼\n'
                '· 因此無法用來登入遊戲，也無法更改帳密，Cookie內容大概長這樣：'
                '`ltoken=xxxx ltuid=1234 cookie_token=yyyy account_id=1122`\n'
                '· 小幫手保存並使用Cookie是為了在Hoyolab網站上取得你的原神資料並提供服務\n'
                '· 小幫手將資料保存於雲端主機獨立環境，只與Discord、Hoyolab伺服器連線\n'
                '· 更詳細說明可以點擊小幫手個人檔案到巴哈說明文查看，若仍有疑慮請不要使用小幫手\n'
                '· 當提交Cookie給小幫手時，表示你已同意小幫手保存並使用你的資料\n'
                '· 你可以隨時刪除保存在小幫手的資料，請使用 `/清除資料` 指令\n')
            embed = discord.Embed(title='小幫手Cookie使用與保存告知', description=msg)
            await interaction.response.send_message(embed=embed)

    # 設定原神UID，當帳號內有多名角色時，保存指定的UID
    @app_commands.command(
        name='uid設定',
        description='帳號內多角色時需保存指定的UID，只有單一角色不需要使用本指令')
    @app_commands.describe(uid='請輸入要保存的「原神」主要角色UID')
    async def slash_uid(self, interaction: discord.Interaction, uid: int):
        await interaction.response.defer(ephemeral=True)
        result = await genshin_app.setUID(str(interaction.user.id), str(uid), check_uid=True)
        await interaction.edit_original_message(content=result)

    # 清除資料確認按紐
    class ConfirmButton(discord.ui.View):
        def __init__(self, *, timeout: Optional[float] = 30):
            super().__init__(timeout=timeout)
            self.value = None
        
        @discord.ui.button(label='取消', style=discord.ButtonStyle.grey)
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
        view = self.ConfirmButton()
        await interaction.response.send_message('是否確定刪除？', view=view, ephemeral=True)
        
        await view.wait()
        if view.value == True:
            result = genshin_app.clearUserData(str(interaction.user.id))
            await interaction.edit_original_message(content=result, view=None)
        else:
            await interaction.edit_original_message(content='取消指令', view=None)

async def setup(client: commands.Bot):
    await client.add_cog(Setting(client))