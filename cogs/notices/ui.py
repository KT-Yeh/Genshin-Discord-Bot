import datetime
from typing import Optional, Sequence

import discord
import genshin

from genshin_py import parser
from utility import EmbedTemplate, config


class Dropdown(discord.ui.Select):
    """選擇公告的下拉選單"""

    def __init__(self, notices: Sequence[genshin.models.Announcement], placeholder: str):
        self.notices = notices
        options = [
            discord.SelectOption(label=notice.subtitle, description=notice.title, value=str(i))
            for i, notice in enumerate(notices)
        ]
        super().__init__(placeholder=placeholder, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        notice = self.notices[int(self.values[0])]
        embed = EmbedTemplate.normal(parser.parse_html_content(notice.content), title=notice.title)
        embed.set_image(url=notice.banner)
        await interaction.response.edit_message(content=None, embed=embed)


class View(discord.ui.View):
    def __init__(self):
        self.last_response_time: Optional[datetime.datetime] = None
        super().__init__(timeout=config.discord_view_long_timeout)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # 避免短時間內太多人按導致聊天版面混亂
        if (
            self.last_response_time is not None
            and (interaction.created_at - self.last_response_time).seconds < 3
        ):
            await interaction.response.send_message(
                embed=EmbedTemplate.normal("短時間內(太多人)點選，請稍後幾秒再試..."), ephemeral=True
            )
            return False
        else:
            self.last_response_time = interaction.created_at
            return True
