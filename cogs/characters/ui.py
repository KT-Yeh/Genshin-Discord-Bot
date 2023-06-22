from typing import Sequence, Union

import discord
import genshin

from genshin_py import parser
from utility import config, emoji


class Dropdown(discord.ui.Select):
    """選擇角色的下拉選單"""

    def __init__(
        self,
        user: Union[discord.User, discord.Member],
        characters: Sequence[genshin.models.Character],
        index: int = 1,
    ):
        options = [
            discord.SelectOption(
                label=f"★{c.rarity} C{c.constellation} Lv.{c.level} {c.name}",
                description=(
                    f"★{c.weapon.rarity} R{c.weapon.refinement} "
                    f"Lv.{c.weapon.level} {c.weapon.name}"
                ),
                value=str(i),
                emoji=emoji.elements.get(c.element.lower()),
            )
            for i, c in enumerate(characters)
        ]
        super().__init__(
            placeholder=f"選擇角色 (第 {index}~{index + len(characters) - 1} 名)",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user = user
        self.characters = characters

    async def callback(self, interaction: discord.Interaction):
        embed = parser.parse_character(self.characters[int(self.values[0])])
        embed.set_author(
            name=f"{self.user.display_name} 的角色一覽",
            icon_url=self.user.display_avatar.url,
        )
        await interaction.response.edit_message(content=None, embed=embed)


class DropdownView(discord.ui.View):
    """顯示角色下拉選單的View，依照選單欄位上限25個分割選單"""

    def __init__(
        self,
        user: Union[discord.User, discord.Member],
        characters: Sequence[genshin.models.Character],
    ):
        super().__init__(timeout=config.discord_view_long_timeout)
        max_row = 25
        for i in range(0, len(characters), max_row):
            self.add_item(Dropdown(user, characters[i : i + max_row], i + 1))
