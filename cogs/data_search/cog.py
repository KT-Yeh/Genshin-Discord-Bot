import random
from typing import Iterable, List, Literal

import discord
import sentry_sdk
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import genshin_db
from utility import EmbedTemplate, config, custom_log

from .ui import SearchResultsDropdown

StrCategory = Literal["角色", "武器", "聖遺物", "物品/食物", "成就", "七聖召喚"]


class Search(commands.Cog, name="資料搜尋"):
    def __init__(self, bot: commands.Bot, genshin_db_data: genshin_db.GenshinDbAllData):
        self.bot = bot
        self.db = genshin_db_data

    @app_commands.command(name="search搜尋資料庫", description="搜尋原神資料庫，包含了角色、武器、各項物品、成就、七聖召喚")
    @app_commands.rename(category="類別", item_name="名稱")
    @app_commands.describe(category="選擇要搜尋的類別")
    @app_commands.choices(
        category=[
            Choice(name="角色", value="角色"),
            Choice(name="武器", value="武器"),
            Choice(name="聖遺物", value="聖遺物"),
            Choice(name="物品/食物", value="物品/食物"),
            Choice(name="成就", value="成就"),
            Choice(name="七聖召喚", value="七聖召喚"),
        ]
    )
    @custom_log.SlashCommandLogger
    async def slash_search(
        self,
        interaction: discord.Interaction,
        category: StrCategory,
        item_name: str,
    ):
        """搜尋 genshin-db 資料庫斜線指令"""
        titles: list[str] = []
        embeds: list[discord.Embed] = []
        match category:
            case "角色":
                character = self.db.characters.find(item_name)
                titles.append("基本資料")
                embeds.append(genshin_db.parse(character))

                # 旅行者多元素特殊處理
                if "旅行者" in item_name:
                    for element in ["風", "岩", "雷", "草"]:
                        talent = self.db.talents.find(f"旅行者 ({element}元素)")
                        titles.append(f"天賦：{element}")
                        embeds.append(genshin_db.parse(talent))
                    for element in ["風", "岩", "雷", "草"]:
                        constell = self.db.constellations.find(f"旅行者 ({element}元素)")
                        titles.append(f"命座：{element}")
                        embeds.append(genshin_db.parse(constell))
                else:
                    talent = self.db.talents.find(item_name)
                    titles.append("天賦")
                    embeds.append(genshin_db.parse(talent))
                    constell = self.db.constellations.find(item_name)
                    titles.append("命座")
                    embeds.append(genshin_db.parse(constell))
            case "聖遺物":
                artifact = self.db.artifacts.find(item_name)
                if artifact is None:
                    return
                titles = ["總覽"]
                embeds = [genshin_db.parse(artifact)]
                _titles = ["花", "羽", "沙", "杯", "頭"]
                _parts = [
                    artifact.flower,
                    artifact.plume,
                    artifact.sands,
                    artifact.goblet,
                    artifact.circlet,
                ]
                for i, _part in enumerate(_parts):
                    if _part is not None:
                        titles.append(_titles[i])
                        embeds.append(genshin_db.parse(_part))
            case _:
                item = self.db.find(item_name)
                embeds.append(genshin_db.parse(item))

        match len(embeds):
            case 0:
                _embed = EmbedTemplate.error("發生錯誤，找不到此項目")
                await interaction.response.send_message(embed=_embed)
            case 1:
                await interaction.response.send_message(embed=embeds[0])
            case n if n > 1:
                view = discord.ui.View(timeout=config.discord_view_long_timeout)
                view.add_item(SearchResultsDropdown(titles, embeds))
                await interaction.response.send_message(embed=embeds[0], view=view)

    @slash_search.autocomplete("item_name")
    async def autocomplete_search_item_name(
        self, interaction: discord.Interaction, current: str
    ) -> List[Choice[str]]:
        """自動完成 slash_search 指令的 item_name 參數"""

        # The key names come from the raw Discord data,
        # which means that if a parameter was renamed then the
        # renamed key is used instead of the function parameter name.
        category: StrCategory | None = interaction.namespace.類別
        if category is None:
            return []

        item_list: Iterable[genshin_db.GenshinDbBase] = {
            "角色": self.db.characters.list,
            "武器": self.db.weapons.list,
            "聖遺物": self.db.artifacts.list,
            "物品/食物": self.db.materials.list + self.db.foods.list,
            "成就": self.db.achievements.list,
            "七聖召喚": self.db.tcg_cards.list,
        }.get(category, [])

        choices: List[Choice[str]] = []
        for item in item_list:
            if current.lower() in item.name.lower():
                choices.append(Choice(name=item.name, value=item.name))
        # 使用者沒輸入的情況下，隨機找 25 個
        if current == "":
            choices = random.sample(choices, k=25)

        choices = choices[:25]
        choices.sort(key=lambda choice: choice.name)
        return choices


async def setup(client: commands.Bot):
    try:
        gdb_data = await genshin_db.fetch_all()
    except Exception as e:
        custom_log.LOG.Error(str(e))
        sentry_sdk.capture_exception(e)
    else:
        await client.add_cog(Search(client, gdb_data))
