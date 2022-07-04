import discord
import asyncio
import re
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from utility.GenshinApp import genshin_app

class GenshinTool(commands.Cog, name='原神工具'):
    def __init__(self, bot):
        self.bot = bot
    
    # 為使用者使用指定的兌換碼
    @app_commands.command(
        name='redeem兌換',
        description='使用Hoyolab兌換碼')
    @app_commands.rename(code='兌換碼')
    @app_commands.describe(code='請輸入要使用的兌換碼，支援多組兌換碼同時輸入')
    async def slash_redeem(self, interaction: discord.Interaction, code: str):
        # 匹配多組兌換碼並存成list
        codes = re.findall(r"[A-Za-z0-9]{3,30}", code)
        if len(codes) == 0:
            await interaction.response.send_message('沒有偵測到兌換碼，請重新輸入')
            return
        asyncio.create_task(interaction.response.defer())
        codes = codes[:5] if len(codes) > 5 else codes  # 避免使用者輸入過多內容
        msg = ''
        for i, code in enumerate(codes):
            # 使用兌換碼的間隔為5秒
            if i > 0:
                await interaction.edit_original_message(embed=discord.Embed(color=0xfcc766, description=f"{msg}正在等待5秒冷卻時間使用第{i+1}組兌換碼..."))
                await asyncio.sleep(5)
            try:
                result = await genshin_app.redeemCode(str(interaction.user.id), code)
            except Exception as e:
                result = str(e)
            if len(result) > 0:
                msg += f"{code} {result}\n"
            else:
                # 兌換網頁無任何回應訊息時，則新增連結按鈕至官網兌換，並結束本函式
                view = discord.ui.View()
                for code in codes:
                    view.add_item(discord.ui.Button(label=code, url=f"https://genshin.hoyoverse.com/gift?code={code}"))
                await interaction.edit_original_message(content='使用過程中發生錯誤，請直接點擊按鈕至官網兌換', view=view)
                return
        await interaction.edit_original_message(embed=discord.Embed(color=0x8fce00, description=msg))

    # 為使用者在Hoyolab簽到
    @app_commands.command(
        name='daily每日簽到',
        description='領取Hoyolab每日簽到獎勵')
    @app_commands.rename(game='遊戲')
    @app_commands.choices(game=[
        Choice(name='原神', value=0), 
        Choice(name='原神 + 崩壞3', value=1)])
    async def slash_daily(self, interaction: discord.Interaction, game: int = 0):
        asyncio.create_task(interaction.response.defer())
        result = await genshin_app.claimDailyReward(str(interaction.user.id), honkai=bool(game))
        await interaction.edit_original_message(content=result)

async def setup(client: commands.Bot):
    await client.add_cog(GenshinTool(client))