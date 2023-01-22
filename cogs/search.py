import random
from typing import List

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from utility import EmbedTemplate
from yuanshen import genius_invokation
from yuanshen.genius_invokation import parser as tcg_parser


class Search(commands.Cog):
    def __init__(self, bot: commands.Bot, tcg_cards: genius_invokation.TCGCards):
        self.bot = bot
        self.tcg_cards = tcg_cards

    @app_commands.command(name="tcg卡牌搜尋", description="搜尋七聖召喚卡牌")
    @app_commands.rename(card_name="名稱")
    async def slash_tcg_cards(self, interaction: discord.Interaction, card_name: str):
        if _character := self.tcg_cards.character_name_card.get(card_name):
            embed = tcg_parser.parse_character_card(_character)
        elif _action := self.tcg_cards.action_name_card.get(card_name):
            embed = tcg_parser.parse_action_card(_action)
        else:
            embed = EmbedTemplate.error(f"找不到卡牌：{card_name}")

        await interaction.response.send_message(embed=embed)

    @slash_tcg_cards.autocomplete("card_name")
    async def autocomplete_tcg_card_name_callback(
        self, interaction: discord.Interaction, current: str
    ) -> List[Choice[str]]:
        choices: List[Choice[str]] = []
        cards = self.tcg_cards.characters + self.tcg_cards.actions
        for card in cards:
            if current.lower() in card.name.lower():
                choices.append(Choice(name=card.name, value=card.name))
        # 使用者沒輸入的情況下，隨機找 20 張不重複的牌
        if current == "":
            choices = random.sample(choices, k=20)
        # 取前 20 張牌並依照名稱排序
        choices = choices[:20]
        choices.sort(key=lambda choice: choice.name)
        return choices


async def setup(client: commands.Bot):
    tcg_cards = await genius_invokation.fetch_cards()
    if tcg_cards:
        await client.add_cog(Search(client, tcg_cards))