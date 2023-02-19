import asyncio
import typing

import discord
import genshin
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from data.database import db
from genshin_py import genshin_app
from utility import EmbedTemplate, config, custom_log, get_app_command_mention, get_server_name


class Setting(commands.Cog, name="設定"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 提交Cookie的表單
    class CookieModal(discord.ui.Modal, title="提交Cookie"):
        cookie = discord.ui.TextInput(
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

    # 設定使用者Cookie
    @app_commands.command(name="cookie設定", description="設定Cookie，第一次使用前必須先使用本指令設定Cookie")
    @app_commands.rename(option="選項")
    @app_commands.choices(
        option=[
            Choice(name="① 顯示說明如何取得Cookie", value=0),
            Choice(name="② 提交已取得的Cookie給小幫手", value=1),
            Choice(name="③ 顯示小幫手Cookie使用與保存告知", value=2),
        ]
    )
    @custom_log.SlashCommandLogger
    async def slash_cookie(self, interaction: discord.Interaction, option: int):
        if option == 0:
            embed = EmbedTemplate.normal(
                "**1.** 先複製本文最底下整段程式碼\n"
                "**2.** PC或手機使用 **Chrome** 開啟 [HoYoVerse官網](https://genshin.hoyoverse.com/"
                "zh-tw/gift)，並從右上角登入帳號 (若是已登入狀態，請先手動登出然後重新登入)\n"
                "**3.** 如下圖，在網址列輸入 `java`，然後貼上程式碼\n"
                "**4.** 按 Enter，網頁會變成顯示你的 Cookie，全選然後複製\n"
                f"**5.** 在這裡使用指令 {get_app_command_mention('cookie設定')} 提交已取得的Cookie\n"
                "． 遇到問題嗎？點 [教學連結](https://bit.ly/3LgQkg0) 查看其他方法\n",
                title="原神小幫手 | 取得Cookie說明",
            )
            embed.set_image(url="https://i.imgur.com/OQ8arx0.gif")
            code_msg = "script: document.write(document.cookie)"
            await interaction.response.send_message(embed=embed)
            await interaction.followup.send(content=code_msg)
        elif option == 1:
            await interaction.response.send_modal(self.CookieModal())
        elif option == 2:
            msg = (
                "· Cookie的內容包含你個人的識別代碼，不包含帳號與密碼\n"
                "· 因此無法用來登入遊戲，也無法更改帳密，Cookie內容大概長這樣："
                "`ltoken=xxxx ltuid=1234 cookie_token=yyyy account_id=1234`\n"
                "· 小幫手保存並使用Cookie是為了在Hoyolab網站上取得你的原神資料並提供服務\n"
                "· 小幫手將資料保存於雲端主機獨立環境，只與Discord、Hoyolab伺服器連線\n"
                "· 更詳細說明可以到 [巴哈說明文](https://forum.gamer.com.tw/Co.php?bsn=36730&sn=162433) 查看，"
                "若仍有疑慮請不要使用小幫手\n"
                "· 當提交Cookie給小幫手時，表示你已同意小幫手保存並使用你的資料\n"
                f'· 你可以隨時刪除保存在小幫手的資料，請使用 {get_app_command_mention("清除資料")} 指令\n'
            )
            embed = EmbedTemplate.normal(msg, title="小幫手Cookie使用與保存告知")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # 選擇欲保存UID的下拉選單
    class UidDropdown(discord.ui.Select):
        def __init__(self, accounts: typing.Sequence[genshin.models.GenshinAccount]):
            options = [
                discord.SelectOption(
                    label=f"[{get_server_name(str(account.uid)[0])}] {account.uid}",
                    description=f"Lv.{account.level} {account.nickname}",
                    value=str(i),
                )
                for i, account in enumerate(accounts)
            ]
            super().__init__(placeholder="請選擇要保存的UID：", options=options)
            self.accounts = accounts

        async def callback(self, interaction: discord.Interaction):
            uid = self.accounts[int(self.values[0])].uid
            await db.users.update(interaction.user.id, uid=uid)
            await interaction.response.edit_message(
                embed=EmbedTemplate.normal(f"角色UID: {uid} 已設定完成"), view=None
            )

    # 設定原神UID，當帳號內有多名角色時，保存指定的UID
    @app_commands.command(name="uid設定", description="帳號內多角色時需保存指定的UID，只有單一角色不需要使用本指令")
    @custom_log.SlashCommandLogger
    async def slash_uid(self, interaction: discord.Interaction):
        try:
            defer, accounts = await asyncio.gather(
                interaction.response.defer(ephemeral=True),
                genshin_app.get_game_accounts(interaction.user.id),
            )
            if len(accounts) == 0:
                raise Exception("此帳號內沒有任何原神角色")
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            view = discord.ui.View(timeout=config.discord_view_short_timeout)
            view.add_item(self.UidDropdown(accounts))
            await interaction.edit_original_response(view=view)

    # 清除資料確認按紐
    class ConfirmButton(discord.ui.View):
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

    # 刪除已保存的個人資料
    @app_commands.command(name="清除資料", description="刪除使用者所有保存在小幫手內的個人資料")
    @custom_log.SlashCommandLogger
    async def slash_clear(self, interaction: discord.Interaction):
        view = self.ConfirmButton()
        await interaction.response.send_message("是否確定刪除？", view=view, ephemeral=True)

        await view.wait()
        if view.value is True:
            await db.removeUser(interaction.user.id)
            await interaction.edit_original_response(content="使用者資料已全部刪除", view=None)
        else:
            await interaction.edit_original_response(content="取消指令", view=None)


async def setup(client: commands.Bot):
    await client.add_cog(Setting(client))
