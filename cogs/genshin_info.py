import datetime
import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from utility.config import config
from utility.GenshinApp import genshin_app

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

    @app_commands.command(
        name='g',
        description='查詢原神即時便箋，包含樹脂、洞天寶錢...等')
    async def slash_g(self, interaction: discord.Interaction):
        result = await genshin_app.getRealtimeNote(str(interaction.user.id))
        embed = discord.Embed(title='', description=result, color=0xFF5733)
        await interaction.response.send_message(embed=embed)
    
    # 取得深境螺旋資訊
    @commands.command(
        brief='查詢深境螺旋紀錄',
        description='查詢深境螺旋紀錄',
        usage='[p] [f] [UID]',
        help='參數 p 查詢上期紀錄、參數 f 顯示全部樓層人物紀錄(預設只顯示最後一層)，範例：\n\n'
            f'{config.bot_prefix}abyss　　　　　　　查詢自己本期紀錄\n'
            f'{config.bot_prefix}abyss p　　　　　　查詢自己上期紀錄\n'
            f'{config.bot_prefix}abyss f　　　　　　查詢自己本期全部樓層紀錄\n'
            f'{config.bot_prefix}abyss p f 123456　查詢123456的上期完整深淵紀錄\n'
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

    @app_commands.command(
        name='abyss',
        description='查詢深境螺旋紀錄')
    @app_commands.describe(
        season='選擇本期或是上期紀錄',
        full_floor='是否顯示全部樓層人物紀錄')
    @app_commands.choices(
        season=[
            Choice(name='本期紀錄', value=0),
            Choice(name='上期紀錄', value=-1)],
        full_floor=[
            Choice(name='只顯示最後一層', value=0),
            Choice(name='顯示全部樓層', value=1)])
    async def slash_abyss(self, interaction: discord.Interaction, season: int = 0, full_floor: int = 0):
        previous = True if season == -1 else False
        full_data = True if full_floor == 1 else False
        result = await genshin_app.getSpiralAbyss(str(interaction.user.id), None, previous, full_data)
        if type(result) == discord.Embed:
            await interaction.response.send_message(embed=result)
        else:
            await interaction.response.send_message(result)

    # 取得使用者旅行者札記
    @commands.command(
        brief='查詢旅行者札記(三個月內)',
        description='查詢旅行者札記',
        usage='[月份]',
        help='月份參數為數字，查詢該月份的旅行者札記，最多只能查到前二個月，範例：\n\n'
            f'{config.bot_prefix}diary　　查詢當月的旅行者札記\n'
            f'{config.bot_prefix}diary 5　查詢5月的旅行者札記'
    )
    async def diary(self, ctx, *month):
        month = month[0] if len(month) > 0 else datetime.datetime.now().month
        result = await genshin_app.getTravelerDiary(ctx.author.id, month)
        if type(result) == discord.Embed:
            await ctx.reply(embed=result)
        else:
            await ctx.reply(result)
    
    @app_commands.command(
        name='diary',
        description='查詢旅行者札記(原石、摩拉收入)')
    @app_commands.describe(
        month='選擇月份')
    @app_commands.choices(
        month=[Choice(name='這個月', value=0), Choice(name='上個月', value=-1), Choice(name='上上個月', value=-2)])
    async def slash_diary(self, interaction: discord.Interaction, month: int = 0):
        month = datetime.datetime.now().month + month
        month = month + 12 if month < 1 else month
        result = await genshin_app.getTravelerDiary(str(interaction.user.id), str(month))
        if type(result) == discord.Embed:
            await interaction.response.send_message(embed=result)
        else:
            await interaction.response.send_message(result)

async def setup(client: commands.Bot):
    await client.add_cog(GenshinInfo(client))