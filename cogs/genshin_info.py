import datetime
import discord
import genshin
from typing import Sequence
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from utility.GenshinApp import genshin_app
from utility.draw import drawRecordCard, drawAbyssCard
from utility.utils import log
from utility.config import config
from utility.emoji import emoji

class GenshinInfo(commands.Cog, name='原神資訊'):
    def __init__(self, bot):
        self.bot = bot

    # 取得使用者即時便箋資訊(樹脂、洞天寶錢、派遣...等)
    @app_commands.command(
        name='notes即時便箋',
        description='查詢即時便箋，包含樹脂、洞天寶錢、探索派遣...等')
    async def slash_notes(self, interaction: discord.Interaction):
        result = await genshin_app.getRealtimeNote(str(interaction.user.id))
        if isinstance(result, str):
            await interaction.response.send_message(result)
        else:
            await interaction.response.send_message(embed=result)
    
    # 取得深境螺旋資訊
    @app_commands.command(
        name='abyss深淵紀錄',
        description='查詢深境螺旋紀錄')
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
    @app_commands.rename(season='時間', floor='樓層')
    @app_commands.describe(
        season='選擇本期或是上期紀錄',
        floor='選擇樓層人物紀錄顯示方式')
    @app_commands.choices(
        season=[Choice(name='上期紀錄', value=0),
                Choice(name='本期紀錄', value=1)],
        floor=[Choice(name='[文字] 顯示全部樓層', value=0),
               Choice(name='[文字] 只顯示最後一層', value=1),
               Choice(name='[圖片] 只顯示最後一層', value=2)])
    async def slash_abyss(self, interaction: discord.Interaction, season: int = 1, floor: int = 2):
        await interaction.response.defer()
        previous = True if season == 0 else False
        result = await genshin_app.getSpiralAbyss(str(interaction.user.id), previous)
        if isinstance(result, str):
            await interaction.edit_original_message(content=result)
            return

        embed = genshin_app.parseAbyssOverview(result)
        embed.title = f'{interaction.user.display_name} 的深境螺旋戰績'
        if floor == 0: # [文字] 顯示全部樓層
            embed = genshin_app.parseAbyssFloor(embed, result, True)
            await interaction.edit_original_message(embed=embed)
        elif floor == 1: # [文字] 只顯示最後一層
            embed = genshin_app.parseAbyssFloor(embed, result, False)
            await interaction.edit_original_message(embed=embed)
        elif floor == 2: # [圖片] 只顯示最後一層
            try:
                fp = drawAbyssCard(result)
            except Exception as e:
                log.error(f'[例外][{interaction.user.id}][slash_abyss]: {e}')
                await interaction.edit_original_message(content='發生錯誤，圖片製作失敗')
            else:
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                fp.seek(0)
                file = discord.File(fp, filename='image.jpeg')
                embed.set_image(url='attachment://image.jpeg')
                await interaction.edit_original_message(embed=embed, attachments=[file])
    
    @slash_abyss.error
    async def on_slash_abyss_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f'使用指令的間隔為{config.slash_cmd_cooldown}秒，請稍後再使用~', ephemeral=True)

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
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
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
            await interaction.response.send_message(f'產生卡片的間隔為{config.slash_cmd_cooldown}秒，請稍後再使用~', ephemeral=True)

    class CharactersDropdown(discord.ui.Select):
        """選擇角色的下拉選單"""
        def __init__(self, previous_interaction: discord.Interaction, characters: Sequence[genshin.models.Character], index: int = 1):
            options = [discord.SelectOption(
                    label=f'★{character.rarity} Lv.{character.level} {character.name}',
                    value=str(i),
                    emoji=emoji.elements.get(character.element.lower())
                ) for i, character in enumerate(characters)
            ]
            super().__init__(placeholder=f'選擇角色 (第 {index}~{index + len(characters) - 1} 名)', min_values=1, max_values=1, options=options)
            self.characters = characters
            self.previous_interaction = previous_interaction
        
        async def callback(self, interaction: discord.Interaction):
            try:
                await interaction.response.defer()
                embed = genshin_app.parseCharacter(self.characters[int(self.values[0])])
                embed.title = f'{self.previous_interaction.user.display_name} 的角色一覽'
                await self.previous_interaction.edit_original_message(content=None, embed=embed)
            except Exception as e:
                log.info(f'[例外][{interaction.user.id}]CharactersDropdown > callback: {e}')
    
    class CharactersDropdownView(discord.ui.View):
        """顯示角色下拉選單的View，依照選單欄位上限25個分割選單"""
        def __init__(self, previous_interaction: discord.Interaction, characters: Sequence[genshin.models.Character]):
            super().__init__(timeout=180)
            max_row = 25
            for i in range(0, len(characters), max_row):
                self.add_item(GenshinInfo.CharactersDropdown(previous_interaction, characters[i:i+max_row], i+1))
    
    # 個人所有角色一覽
    @app_commands.command(name='character角色一覽', description='公開展示我的所有角色')
    async def slash_character(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await genshin_app.getCharacters(str(interaction.user.id))

        if isinstance(result, str):
            await interaction.edit_original_message(content=result)
            return
        
        view = self.CharactersDropdownView(interaction ,result)
        await interaction.edit_original_message(content='請選擇角色：', view=view)
        await view.wait()
        await interaction.edit_original_message(view=None)

async def setup(client: commands.Bot):
    await client.add_cog(GenshinInfo(client))