import datetime
import discord
import genshin
import asyncio
import sentry_sdk
from typing import Optional, Sequence
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from utility.GenshinApp import genshin_app
from utility.draw import drawRecordCard, drawAbyssCard
from utility.utils import log, EmbedTemplate
from utility.config import config
from utility.emoji import emoji
from utility import Enka

class RealtimeNotes:
    """即時便箋"""
    @staticmethod
    async def notes(interaction: discord.Interaction, user: discord.User, *, shortForm: bool = False):
        try:
            defer, notes = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.getRealtimeNote(str(user.id))
            )
        except Exception as e:
            await interaction.edit_original_message(embed=EmbedTemplate.error(str(e)))
        else:
            embed = genshin_app.parseNotes(notes, user=user, shortForm=shortForm)
            await interaction.edit_original_message(embed=embed)

class SpiralAbyss:
    """深境螺旋"""
    class AuthorOnlyView(discord.ui.View):
        """只有原本Interaction使用者才能使用的View"""
        def __init__(self, author: discord.Member, timeout: float):
            self.author = author
            super().__init__(timeout=timeout)
        
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id
    
    class AbyssFloorDropdown(discord.ui.Select):
        """選擇深淵樓層的下拉選單"""
        def __init__(self, overview: discord.Embed, floors: Sequence[genshin.models.Floor]):
            options = [discord.SelectOption(
                    label=f"[★{floor.stars}] 第 {floor.floor} 層",
                    description=genshin_app.parseAbyssChamber(floor.chambers[-1]),
                    value=str(i)
                ) for i, floor in enumerate(floors)
            ]
            super().__init__(placeholder='選擇樓層：', options=options)
            self.embed = overview
            self.floors = floors
        
        async def callback(self, interaction: discord.Interaction):
            fp = drawAbyssCard(self.floors[int(self.values[0])])
            fp.seek(0)
            self.embed.set_image(url="attachment://image.jpeg")
            await interaction.response.edit_message(embed=self.embed, attachments=[discord.File(fp, "image.jpeg")])
    
    @staticmethod
    async def abyss(interaction: discord.Interaction, user: discord.User, *, previous: bool = False):
        try:
            defer, abyss = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.getSpiralAbyss(str(user.id), previous)
            )
        except Exception as e:
            await interaction.edit_original_message(embed=EmbedTemplate.error(str(e)))
        else:
            embed = genshin_app.parseAbyssOverview(abyss)
            embed.title = f'{user.display_name} 的深境螺旋戰績'
            embed.set_thumbnail(url=user.display_avatar.url)
            view = None
            if len(abyss.floors) > 0:
                view = SpiralAbyss.AuthorOnlyView(interaction.user, config.discord_view_long_timeout)
                view.add_item(SpiralAbyss.AbyssFloorDropdown(embed, abyss.floors))
            await interaction.edit_original_message(embed=embed, view=view)

class TravelerDiary:
    """旅行者札記"""
    @staticmethod
    async def diary(interaction: discord.Interaction, user: discord.User, month: int):
        try:
            defer, embed = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.getTravelerDiary(str(user.id), month)
            )
        except Exception as e:
            await interaction.edit_original_message(embed=EmbedTemplate.error(str(e)))
        else:
            embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.edit_original_message(embed=embed)

class RecordCard:
    """遊戲紀錄卡片"""
    @staticmethod
    async def card(interaction: discord.Interaction, user: discord.User):
        try:
            defer, (card, userstats) = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.getRecordCard(str(user.id))
            )
        except Exception as e:
            await interaction.edit_original_message(embed=EmbedTemplate.error(str(e)))
            return
        
        try:
            avatar_bytes = await user.display_avatar.read()
            fp = drawRecordCard(avatar_bytes, card, userstats)
        except Exception as e:
            log.warning(f'[例外][{interaction.user.id}][slash_card]: {e}')
            sentry_sdk.capture_exception(e)
            await interaction.edit_original_message(embed=EmbedTemplate.error('發生錯誤，卡片製作失敗'))
        else:
            fp.seek(0)
            await interaction.edit_original_message(attachments=[discord.File(fp=fp, filename='image.jpeg')])
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
                genshin_app.getCharacters(str(user.id))
            )
        except Exception as e:
            await interaction.edit_original_message(embed=EmbedTemplate.error(str(e)))
        else:
            view = Characters.DropdownView(user, characters)
            await interaction.edit_original_message(content='請選擇角色：', view=view)

class Showcase:
    """角色展示櫃"""
    @staticmethod
    async def showcase(interaction: discord.Interaction, user: discord.User, uid: Optional[int] = None):
        await interaction.response.defer()
        uid = uid or genshin_app.getUID(str(user.id))
        log.info(f'[指令][{interaction.user.id}]showcase角色展示櫃: uid={uid}')
        if uid == None:
            await interaction.edit_original_message(embed=EmbedTemplate.error('小幫手內找不到使用者資料，請直接在指令uid參數中輸入欲查詢的UID'))
        elif len(str(uid)) != 9 or str(uid)[0] not in ['1', '2', '5', '6', '7', '8', '9']:
            await interaction.edit_original_message(embed=EmbedTemplate.error('輸入的UID格式錯誤'))
        else:
            showcase = Enka.Showcase(uid)
            try:
                await showcase.getEnkaData()
            except Exception as e:
                log.warning(f'[例外][{interaction.user.id}]showcase角色展示櫃: {e}')
                sentry_sdk.capture_exception(e)
                await interaction.edit_original_message(embed=EmbedTemplate.error(f"{e}，你可以點擊 [連結]({showcase.url}) 查看網站狀態"))
            else:
                view = Enka.ShowcaseView(showcase)
                embed = showcase.getPlayerOverviewEmbed()
                await interaction.edit_original_message(embed=embed, view=view)

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
    async def slash_notes(self, interaction: discord.Interaction, shortForm: int = 0, user: discord.User = None):
        await RealtimeNotes.notes(interaction, user or interaction.user, shortForm=bool(shortForm))
    
    #-------------------------------------------------------------
    # 取得深境螺旋資訊
    @app_commands.command(
        name='abyss深淵紀錄',
        description='查詢深境螺旋紀錄')
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
    @app_commands.rename(season='時間', user='使用者')
    @app_commands.describe(
        season='選擇本期或是上期紀錄',
        user='查詢其他成員的資料，不填寫則查詢自己')
    @app_commands.choices(
        season=[Choice(name='本期紀錄', value=0),
                Choice(name='上期紀錄', value=1)])
    async def slash_abyss(self, interaction: discord.Interaction, season: int, user: discord.User = None):
        await SpiralAbyss.abyss(interaction, user or interaction.user, previous=bool(season))

    @slash_abyss.error
    async def on_slash_abyss_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(embed=EmbedTemplate.error(f'使用指令的間隔為{config.slash_cmd_cooldown}秒，請稍後再使用~'), ephemeral=True)

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
    async def slash_diary(self, interaction: discord.Interaction, month: int):
        month = datetime.datetime.now().month + month
        month = month + 12 if month < 1 else month
        await TravelerDiary.diary(interaction, interaction.user, month)

    #-------------------------------------------------------------
    # 產生遊戲紀錄卡片
    @app_commands.command(name='card紀錄卡片', description='產生原神個人遊戲紀錄卡片')
    @app_commands.rename(user='使用者')
    @app_commands.describe(user='查詢其他成員的資料，不填寫則查詢自己')
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
    async def slash_card(self, interaction: discord.Interaction, user: discord.User = None):
        await RecordCard.card(interaction, user or interaction.user)

    @slash_card.error
    async def on_slash_card_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(embed=EmbedTemplate.error(f'產生卡片的間隔為{config.slash_cmd_cooldown}秒，請稍後再使用~'), ephemeral=True)
    
    #-------------------------------------------------------------
    # 個人所有角色一覽
    @app_commands.command(name='character角色一覽', description='公開展示我的所有角色')
    async def slash_characters(self, interaction: discord.Interaction):
        await Characters.characters(interaction, interaction.user)

    #-------------------------------------------------------------
    # 角色展示櫃
    @app_commands.command(name='showcase角色展示櫃', description='查詢指定UID玩家的公開角色展示櫃')
    @app_commands.rename(user='使用者')
    @app_commands.describe(
        uid='欲查詢的玩家UID，若小幫手已保存資料的話查自己不需要填本欄位',
        user='查詢其他成員的資料，不填寫則查詢自己')
    async def slash_showcase(self, interaction: discord.Interaction, uid: Optional[int] = None, user: discord.User = None):
        await Showcase.showcase(interaction, user or interaction.user, uid)

async def setup(client: commands.Bot):
    await client.add_cog(GenshinInfo(client))
    
    #-------------------------------------------------------------
    # 下面為Context Menu指令
    @client.tree.context_menu(name='即時便箋')
    async def context_notes(interaction: discord.Interaction, user: discord.User):
        await RealtimeNotes.notes(interaction, user)

    @client.tree.context_menu(name='深淵紀錄(上期)')
    async def context_abyss_previous(interaction: discord.Interaction, user: discord.User):
        await SpiralAbyss.abyss(interaction, user, previous=True)

    @client.tree.context_menu(name='深淵紀錄(本期)')
    async def context_abyss(interaction: discord.Interaction, user: discord.User):
        await SpiralAbyss.abyss(interaction, user)

    @client.tree.context_menu(name='遊戲紀錄卡片')
    async def context_card(interaction: discord.Interaction, user: discord.User):
        await RecordCard.card(interaction, user)

    @client.tree.context_menu(name='角色展示櫃')
    async def context_showcase(interaction: discord.Interaction, user: discord.User):
        await Showcase.showcase(interaction, user, None)
