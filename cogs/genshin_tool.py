import discord
import asyncio
import re
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from utility.GenshinApp import genshin_app
from utility.utils import EmbedTemplate
from utility import CustomLog

class RedeemCode:
    """使用兌換碼"""
    @staticmethod
    async def redeem(interaction: discord.Interaction, user: discord.User, code: str):
        # 若兌換碼包含兌換網址，則移除該網址
        code = re.sub(r"(https://){0,1}genshin.hoyoverse.com(/.*){0,1}/gift\?code=", '', code)
        # 匹配多組兌換碼並存成list
        codes = re.findall(r"[A-Za-z0-9]{3,30}", code)
        if len(codes) == 0:
            await interaction.response.send_message(embed=EmbedTemplate.error('沒有偵測到兌換碼，請重新輸入'))
            return
        await interaction.response.defer()
        codes = codes[:5] if len(codes) > 5 else codes  # 避免使用者輸入過多內容
        msg = ''
        for i, code in enumerate(codes):
            # 使用兌換碼的間隔為5秒
            if i > 0:
                await interaction.edit_original_response(embed=discord.Embed(color=0xfcc766, description=f"{msg}正在等待5秒冷卻時間使用第{i+1}組兌換碼..."))
                await asyncio.sleep(5)
            try:
                result = '✅' + await genshin_app.redeemCode(user.id, code)
            except Exception as e:
                result = '❌' + str(e)
            msg += f"[{code}](https://genshin.hoyoverse.com/gift?code={code})：{result}\n"
        
        embed = discord.Embed(color=0x8fce00, description=msg)
        embed.set_footer(text='點擊上述兌換碼可代入兌換碼至官網兌換')
        await interaction.edit_original_response(embed=embed)

class GenshinTool(commands.Cog, name='原神工具'):
    """斜線指令"""
    def __init__(self, bot):
        self.bot = bot
    
    # 為使用者使用指定的兌換碼
    @app_commands.command(
        name='redeem兌換',
        description='使用Hoyolab兌換碼')
    @app_commands.rename(code='兌換碼', user='使用者')
    @app_commands.describe(code='請輸入要使用的兌換碼，支援多組兌換碼同時輸入')
    @CustomLog.SlashCommandLogger
    async def slash_redeem(self, interaction: discord.Interaction, code: str, user: discord.User = None):
        await RedeemCode.redeem(interaction, user or interaction.user, code)

    # 為使用者在Hoyolab簽到
    @app_commands.command(
        name='daily每日簽到',
        description='領取Hoyolab每日簽到獎勵')
    @app_commands.rename(game='遊戲', user='使用者')
    @app_commands.choices(game=[
        Choice(name='原神', value=0), 
        Choice(name='原神 + 崩壞3', value=1)])
    @CustomLog.SlashCommandLogger
    async def slash_daily(self, interaction: discord.Interaction, game: int = 0, user: discord.User = None):
        user = user or interaction.user
        defer, result = await asyncio.gather(
            interaction.response.defer(),
            genshin_app.claimDailyReward(user.id, honkai=bool(game))
        )
        await interaction.edit_original_response(embed=EmbedTemplate.normal(result))

async def setup(client: commands.Bot):
    await client.add_cog(GenshinTool(client))

    @client.tree.context_menu(name='使用兌換碼')
    @CustomLog.ContextCommandLogger
    async def context_redeem(interaction: discord.Interaction, msg: discord.Message):
        await RedeemCode.redeem(interaction, interaction.user, msg.content)
