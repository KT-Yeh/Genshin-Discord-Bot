import discord
from discord import app_commands
from discord.ext import commands
from utility.config import config
from utility.GenshinApp import genshin_app

class GenshinTool(commands.Cog, name='原神工具'):
    def __init__(self, bot):
        self.bot = bot

    # 為使用者使用指定的兌換碼
    @commands.command(
        aliases=['R', 'redeem'],
        brief='使用兌換碼',
        description='使用兌換碼',
        usage='<兌換碼>',
        help=f'範例: {config.bot_prefix}R ABCDEFG'
    )
    async def r(self, ctx, code):
        result = await genshin_app.redeemCode(ctx.author.id, code)
        await ctx.reply(result)

    @app_commands.command(
        name='redeem兌換',
        description='使用Hoyolab兌換碼')
    @app_commands.rename(code='兌換碼')
    @app_commands.describe(code='請輸入要使用的兌換碼')
    async def slash_redeem(self, interaction: discord.Interaction, code: str):
        result = await genshin_app.redeemCode(str(interaction.user.id), code)
        await interaction.response.send_message(result)

    # 為使用者在Hoyolab簽到
    @commands.command(
        aliases=['D', 'daily'],
        brief='領取Hoyolab每日簽到獎勵',
        description='領取Hoyolab每日簽到獎勵',
        usage='',
        help=''
    )
    async def d(self, ctx):
        result = await genshin_app.claimDailyReward(ctx.author.id)
        await ctx.reply(result)
    
    @app_commands.command(
        name='daily每日簽到',
        description='領取Hoyolab每日簽到獎勵')
    async def slash_daily(self, interaction: discord.Interaction):
        result = await genshin_app.claimDailyReward(str(interaction.user.id))
        await interaction.response.send_message(result)

async def setup(client: commands.Bot):
    await client.add_cog(GenshinTool(client))