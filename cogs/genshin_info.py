import datetime
import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from utility.GenshinApp import genshin_app
from utility.draw import drawRecordCard
from utility.utils import log

class GenshinInfo(commands.Cog, name='原神資訊'):
    def __init__(self, bot):
        self.bot = bot

    # 取得使用者即時便箋資訊(樹脂、洞天寶錢、派遣...等)
    @app_commands.command(
        name='notes即時便箋',
        description='查詢即時便箋，包含樹脂、洞天寶錢、探索派遣...等')
    async def slash_notes(self, interaction: discord.Interaction):
        result = await genshin_app.getRealtimeNote(str(interaction.user.id))
        embed = discord.Embed(title='', description=result[1], color=0xFF785B)
        await interaction.response.send_message(embed=embed)
    
    # 取得深境螺旋資訊
    @app_commands.command(
        name='abyss深淵紀錄',
        description='查詢深境螺旋紀錄')
    @app_commands.rename(season='時間', floor='樓層')
    @app_commands.describe(
        season='選擇本期或是上期紀錄',
        floor='是否顯示全部樓層人物紀錄')
    @app_commands.choices(
        season=[Choice(name='上期紀錄', value=0),
                Choice(name='本期紀錄', value=1)],
        floor=[Choice(name='顯示全部樓層', value=0),
               Choice(name='只顯示最後一層', value=1)])
    async def slash_abyss(self, interaction: discord.Interaction, season: int = 1, floor: int = 1):
        previous = True if season == 0 else False
        full_data = True if floor == 0 else False
        result = await genshin_app.getSpiralAbyss(str(interaction.user.id), previous, full_data)
        if type(result) == discord.Embed:
            await interaction.response.send_message(embed=result)
        else:
            await interaction.response.send_message(result)

    # 取得使用者旅行者札記
    @app_commands.command(
        name='diary旅行者札記',
        description='查詢旅行者札記(原石、摩拉收入)')
    @app_commands.rename(month='月份')
    @app_commands.describe(month='請選擇要查詢的月份')
    @app_commands.choices(month=[
            Choice(name='這個月', value=0),
            Choice(name='上個月', value=-1),
            Choice(name='上上個月', value=-2)])
    async def slash_diary(self, interaction: discord.Interaction, month: int):
        month = datetime.datetime.now().month + month
        month = month + 12 if month < 1 else month
        result = await genshin_app.getTravelerDiary(str(interaction.user.id), month)
        if type(result) == discord.Embed:
            await interaction.response.send_message(embed=result)
        else:
            await interaction.response.send_message(result)

    # 產生個人紀錄卡片
    @app_commands.command(name='card紀錄卡片', description='產生原神個人遊戲紀錄卡片')
    @app_commands.checks.cooldown(1, 30)
    async def slash_card(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await genshin_app.getRecordCard(str(interaction.user.id))

        if isinstance(result, str):
            await interaction.edit_original_message(content=result)
            return
        
        avatar_bytes = await interaction.user.display_avatar.read()
        card = result[0]
        userstats = result[1]
        try:
            fp = drawRecordCard(avatar_bytes, card, userstats)
        except Exception as e:
            log.error(f'[例外][{interaction.user.id}][slash_card]: {e}')
            await interaction.edit_original_message(content='發生錯誤，卡片製作失敗')
        else:
            fp.seek(0)
            await interaction.edit_original_message(attachments=[discord.File(fp=fp, filename='image.jpeg')])
            fp.close()

    @slash_card.error
    async def on_slash_card_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message('產生卡片的間隔為30秒，請稍後再使用~', ephemeral=True)

async def setup(client: commands.Bot):
    await client.add_cog(GenshinInfo(client))