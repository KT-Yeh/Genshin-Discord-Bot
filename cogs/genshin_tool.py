import discord
from discord.ext import commands
from utility.GenshinApp import genshin_app
import os
from dotenv import load_dotenv
load_dotenv()

class GenshinTool(commands.Cog, name='原神工具'):
    def __init__(self, bot):
        self.bot = bot

    # 為使用者使用指定的兌換碼
    @commands.command(
        aliases=['R', 'redeem'],
        brief='使用兌換碼',
        description='使用兌換碼',
        usage='<兌換碼>',
        help=f'範例: {os.getenv("BOT_PREFIX")}R ABCDEFG'
    )
    async def r(self, ctx, code):
        result = await genshin_app.redeemCode(ctx.author.id, code)
        await ctx.reply(result)

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

def setup(client):
    client.add_cog(GenshinTool(client))