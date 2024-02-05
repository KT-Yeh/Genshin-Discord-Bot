import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from utility import EmbedTemplate, custom_log, get_app_command_mention

from .ui import GameSelectionView


class CookieSettingCog(commands.Cog, name="Cookie 設定"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="cookie設定", description="設定Cookie，第一次使用前必須先使用本指令設定Cookie"
    )
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
        if option == 0:  # 顯示說明如何取得 Cookie
            embed = EmbedTemplate.normal(
                "**1.** 使用 **電腦**瀏覽器 無痕視窗開啟 [HoYoLAB官網](https://www.hoyolab.com) 並登入帳號\n"
                "**2.** 按 **F12** 打開瀏覽器開發者工具\n"
                "**3.** 切換至 **應用程式 (Application)** 頁面 (參考下圖)\n"
                "**4.** 點選左邊 Cookies 底下的網址，右邊就會看到你的 Cookie\n"
                "**5.** 找到 **ltuid_v2**、**ltoken_v2**、**ltmid_v2**，複製這三個欄位的值\n"
                f"**6.** 在這裡使用指令 {get_app_command_mention('cookie設定')} 貼到對應的欄位\n"
                "． 遇到問題嗎？點 >>[詳細教學](https://hackmd.io/66fq-6NsT1Kqxqbpkj1xTA)<< 查看解決方法\n",
                title="原神小幫手 | 取得Cookie說明",
            )
            embed.set_image(url="https://i.imgur.com/tgjWuvy.png")
            await interaction.response.send_message(embed=embed)

        elif option == 1:  # 提交已取得的Cookie給小幫手
            view = GameSelectionView()
            await interaction.response.send_message(
                embed=EmbedTemplate.normal(
                    "請選擇要設定Cookie的遊戲，不同遊戲可以設定不同帳號的Cookie"
                ),
                view=view,
                ephemeral=True,
            )

        elif option == 2:  # 顯示小幫手Cookie使用與保存告知
            msg = (
                "· Cookie的內容包含你個人的識別代碼，不包含帳號與密碼\n"
                "· 因此無法用來登入遊戲，也無法更改帳密，Cookie內容大概長這樣："
                "`ltoken_v2=xxxx ltuid_v2=1234 ltmid_v2=yyyy`\n"
                "· 小幫手保存並使用Cookie是為了在Hoyolab網站上取得你的原神資料並提供服務\n"
                "· 小幫手將資料保存於雲端主機獨立環境，只與Discord、Hoyolab伺服器連線\n"
                "· 更詳細說明可以到 [巴哈說明文](https://forum.gamer.com.tw/Co.php?bsn=36730&sn=162433) 查看，"
                "若仍有疑慮請不要使用小幫手\n"
                "· 當提交Cookie給小幫手時，表示你已同意小幫手保存並使用你的資料\n"
                f'· 你可以隨時刪除保存在小幫手的資料，請使用 {get_app_command_mention("清除資料")} 指令\n'
            )
            embed = EmbedTemplate.normal(msg, title="小幫手Cookie使用與保存告知")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot):
    await client.add_cog(CookieSettingCog(client))
