import datetime
import discord
from discord.ext import commands
from utility.GenshinApp import genshin_app
import os
from dotenv import load_dotenv
load_dotenv()

class GenshinInfo(commands.Cog, name='原神資訊'):
    def __init__(self, bot):
        self.bot = bot

    # 取得使用者即時便箋資訊(樹脂、洞天寶錢、派遣...等)
    @commands.command(
        aliases=['G'], 
        brief='查詢原神即時便箋，包含樹脂、洞天寶錢...等', 
        description='查詢原神即時便箋，包含樹脂、洞天寶錢、派遣探索...等',
        usage='',
        help=''
    )
    async def g(self, ctx, *args):
        msg = await ctx.send('讀取中...')
        user_id = ctx.author.id if len(args) == 0 else filter(str.isdigit, args[0])
        result = await genshin_app.getRealtimeNote(user_id)
        embed = discord.Embed(title='', description=result, color=0xFF5733)
        if ctx.me.guild_permissions.manage_messages:
            await msg.delete()
        await ctx.reply(embed=embed)
    
    # 取得深境螺旋資訊
    @commands.command(
        brief='查詢深境螺旋紀錄',
        description='查詢深境螺旋紀錄',
        usage='[p] [f] [UID]',
        help='參數 p 查詢上期紀錄、參數 f 顯示全部樓層人物紀錄(預設只顯示最後一層)，範例：\n\n'
            f'{os.getenv("BOT_PREFIX")}abyss　　　　　　　查詢自己本期紀錄\n'
            f'{os.getenv("BOT_PREFIX")}abyss p　　　　　　查詢自己上期紀錄\n'
            f'{os.getenv("BOT_PREFIX")}abyss f　　　　　　查詢自己本期全部樓層紀錄\n'
            f'{os.getenv("BOT_PREFIX")}abyss p f 123456　查詢123456的上期完整深淵紀錄\n'
    )
    async def abyss(self, ctx, *args: str):
        previous = False
        full_data = False
        uid = None
        user_id = ctx.author.id
        for arg in args:
            if arg == 'p':
                previous = True
            elif arg == 'f':
                full_data = True
            elif len(arg) < 12 and arg.isnumeric(): # Genshin UID
                uid = arg
            else:   # Discord UID
                user_id = ''.join(filter(str.isdigit, arg))
    
        result = await genshin_app.getSpiralAbyss(user_id, uid, previous, full_data)
        if type(result) == discord.Embed:
            await ctx.reply(embed=result)
        else:
            await ctx.reply(result)

    # 取得使用者旅行者札記
    @commands.command(
        brief='查詢旅行者札記(三個月內)',
        description='查詢旅行者札記',
        usage='[月份]',
        help='月份參數為數字，查詢該月份的旅行者札記，最多只能查到前二個月，範例：\n\n'
            f'{os.getenv("BOT_PREFIX")}diary　　查詢當月的旅行者札記\n'
            f'{os.getenv("BOT_PREFIX")}diary 5　查詢5月的旅行者札記'
    )
    async def diary(self, ctx, *month):
        month = month[0] if len(month) > 0 else datetime.datetime.now().month
        result = await genshin_app.getTravelerDiary(ctx.author.id, month)
        if type(result) == discord.Embed:
            await ctx.reply(embed=result)
        else:
            await ctx.reply(result)

def setup(client):
    client.add_cog(GenshinInfo(client))