import datetime
import discord
import genshin
import asyncio
import sentry_sdk
from typing import Sequence, Literal
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from utility.GenshinApp import genshin_app
from utility.draw import drawRecordCard, drawExplorationCard
from utility.utils import EmbedTemplate
from utility.config import config
from utility.emoji import emoji
from utility.CustomLog import LOG, SlashCommandLogger, ContextCommandLogger

class RealtimeNotes:
    """即時便箋"""
    @staticmethod
    async def notes(interaction: discord.Interaction, user: discord.User, *, shortForm: bool = False):
        try:
            defer, notes = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.getRealtimeNote(user.id)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(str(e)))
        else:
            embed = await genshin_app.parseNotes(notes, user=user, shortForm=shortForm)
            await interaction.edit_original_response(embed=embed)

class TravelerDiary:
    """旅行者札記"""
    @staticmethod
    async def diary(interaction: discord.Interaction, user: discord.User, month: int):
        try:
            defer, embed = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.getTravelerDiary(user.id, month)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(str(e)))
        else:
            embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.edit_original_response(embed=embed)

class RecordCard:
    """遊戲紀錄卡片"""
    @staticmethod
    async def card(interaction: discord.Interaction, user: discord.User, option: Literal['RECORD', 'EXPLORATION']):
        try:
            defer, (uid, userstats) = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.getRecordCard(user.id)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(str(e)))
            return
        
        try:
            avatar_bytes = await user.display_avatar.read()
            if option == 'RECORD':
                fp = drawRecordCard(avatar_bytes, uid, userstats)
            elif option == 'EXPLORATION':
                fp = drawExplorationCard(avatar_bytes, uid, userstats)
        except Exception as e:
            LOG.ErrorLog(interaction, e)
            sentry_sdk.capture_exception(e)
            await interaction.edit_original_response(embed=EmbedTemplate.error('發生錯誤，卡片製作失敗'))
        else:
            fp.seek(0)
            await interaction.edit_original_response(attachments=[discord.File(fp=fp, filename='image.jpeg')])
            fp.close()

class Characters:
    """角色一覽"""
    class Dropdown(discord.ui.Select):
        """選擇角色的下拉選單"""
        def __init__(self, user: discord.User, characters: Sequence[genshin.models.Character], index: int = 1):
            options = [discord.SelectOption(
                    label=f'★{character.rarity} C{character.constellation} Lv.{character.level} {character.name}',
                    description=f'★{character.weapon.rarity} R{character.weapon.refinement} Lv.{character.weapon.level} {character.weapon.name}',
                    value=str(i),
                    emoji=emoji.elements.get(character.element.lower())
                ) for i, character in enumerate(characters)
            ]
            super().__init__(placeholder=f'選擇角色 (第 {index}~{index + len(characters) - 1} 名)', min_values=1, max_values=1, options=options)
            self.user = user
            self.characters = characters
        
        async def callback(self, interaction: discord.Interaction):
            embed = genshin_app.parseCharacter(self.characters[int(self.values[0])])
            embed.set_author(name=f'{self.user.display_name} 的角色一覽', icon_url=self.user.display_avatar.url)
            await interaction.response.edit_message(content=None, embed=embed)

    class DropdownView(discord.ui.View):
        """顯示角色下拉選單的View，依照選單欄位上限25個分割選單"""
        def __init__(self, user: discord.User, characters: Sequence[genshin.models.Character]):
            super().__init__(timeout=config.discord_view_long_timeout)
            max_row = 25
            for i in range(0, len(characters), max_row):
                self.add_item(Characters.Dropdown(user, characters[i:i+max_row], i+1))
    
    @staticmethod
    async def characters(interaction: discord.Interaction, user: discord.User):
        try:
            defer, characters = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.getCharacters(user.id)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(str(e)))
        else:
            view = Characters.DropdownView(user, characters)
            await interaction.edit_original_response(content='請選擇角色：', view=view)

class GenshinInfo(commands.Cog, name='原神資訊'):
    """斜線指令"""
    def __init__(self, bot):
        self.bot = bot

    #-------------------------------------------------------------
    # 取得使用者即時便箋資訊(樹脂、洞天寶錢、派遣...等)
    @app_commands.command(
        name='notes即時便箋',
        description='查詢即時便箋，包含樹脂、洞天寶錢、探索派遣...等')
    @app_commands.rename(shortForm='顯示格式', user='使用者')
    @app_commands.describe(
        shortForm='選擇顯示完整或簡約格式(省略每日、週本、探索派遣)',
        user='查詢其他成員的資料，不填寫則查詢自己')
    @app_commands.choices(
        shortForm=[Choice(name='完整', value=0),
                   Choice(name='簡約', value=1)])
    @SlashCommandLogger
    async def slash_notes(self, interaction: discord.Interaction, shortForm: int = 0, user: discord.User = None):
        await RealtimeNotes.notes(interaction, user or interaction.user, shortForm=bool(shortForm))

    #-------------------------------------------------------------
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
    @SlashCommandLogger
    async def slash_diary(self, interaction: discord.Interaction, month: int):
        month = datetime.datetime.now().month + month
        month = month + 12 if month < 1 else month
        await TravelerDiary.diary(interaction, interaction.user, month)

    #-------------------------------------------------------------
    # 產生遊戲紀錄卡片
    @app_commands.command(name='card紀錄卡片', description='產生原神個人遊戲紀錄卡片')
    @app_commands.rename(option='選項', user='使用者')
    @app_commands.describe(
        option='選擇要查詢數據總覽或是世界探索度',
        user='查詢其他成員的資料，不填寫則查詢自己')
    @app_commands.choices(option=[
        Choice(name='數據總覽', value='RECORD'),
        Choice(name='世界探索', value='EXPLORATION')])
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
    @SlashCommandLogger
    async def slash_card(self, interaction: discord.Interaction, option: str, user: discord.User = None):
        await RecordCard.card(interaction, user or interaction.user, option)

    @slash_card.error
    async def on_slash_card_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(embed=EmbedTemplate.error(f'產生卡片的間隔為{config.slash_cmd_cooldown}秒，請稍後再使用~'), ephemeral=True)
    
    #-------------------------------------------------------------
    # 個人所有角色一覽
    @app_commands.command(name='character角色一覽', description='公開展示我的所有角色')
    @SlashCommandLogger
    async def slash_characters(self, interaction: discord.Interaction):
        await Characters.characters(interaction, interaction.user)

async def setup(client: commands.Bot):
    await client.add_cog(GenshinInfo(client))
    
    #-------------------------------------------------------------
    # 下面為Context Menu指令
    @client.tree.context_menu(name='即時便箋')
    @ContextCommandLogger
    async def context_notes(interaction: discord.Interaction, user: discord.User):
        await RealtimeNotes.notes(interaction, user)

    @client.tree.context_menu(name='遊戲紀錄卡片')
    @ContextCommandLogger
    async def context_card(interaction: discord.Interaction, user: discord.User):
        await RecordCard.card(interaction, user, 'RECORD')
