import discord
from discord.ext import commands
from utility.config import config
from utility.GenshinApp import genshin_app

class GenshinTool(commands.Cog, name='原神工具'):
    def __init__(self, bot):
        self.bot = bot

    # Redeem a code
    @commands.command(
        aliases=['R', 'redeem'],
        brief='使用兌換碼',
        description='使用兌換碼',
        usage='<兌換碼>',
        help=f'範例: {config.bot_prefix}R ABCDEFG'
    )
    async def r(self, ctx, code):
        result = await genshin_app.redeemCode(ctx.author.id, code)
        await ctx.send(result)

    # Claim daily reward
    @commands.command(
        aliases=['D', 'daily'],
        brief='Hololab每日簽到',
        description='Hololab每日簽到',
        usage='',
        help=''
    )
    async def d(self, ctx):
        result = await genshin_app.claimDailyReward(ctx.author.id)
        await ctx.send(result)

def setup(client):
    client.add_cog(GenshinTool(client))