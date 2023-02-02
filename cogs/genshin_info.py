import asyncio
import datetime
from typing import Literal, Optional, Sequence, Union

import discord
import genshin
import sentry_sdk
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from utility import EmbedTemplate, config, emoji
from utility.custom_log import LOG, ContextCommandLogger, SlashCommandLogger
from yuanshen import draw, genshin_app, parser


class RealtimeNotes:
    """即時便箋"""

    @staticmethod
    async def notes(
        interaction: discord.Interaction,
        user: Union[discord.User, discord.Member],
        *,
        shortForm: bool = False,
    ):
        try:
            defer, notes = await asyncio.gather(
                interaction.response.defer(), genshin_app.get_realtime_notes(user.id)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            embed = await parser.parse_realtime_notes(notes, user=user, shortForm=shortForm)
            await interaction.edit_original_response(embed=embed)


class TravelerDiary:
    """旅行者札記"""

    @staticmethod
    async def diary(
        interaction: discord.Interaction, user: Union[discord.User, discord.Member], month: int
    ):
        try:
            defer, diary = await asyncio.gather(
                interaction.response.defer(),
                genshin_app.get_traveler_diary(user.id, month),
            )
            embed = parser.parse_diary(diary, month)
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.edit_original_response(embed=embed)


class RecordCard:
    """遊戲紀錄卡片"""

    @staticmethod
    async def card(
        interaction: discord.Interaction,
        user: Union[discord.User, discord.Member],
        option: Literal["RECORD", "EXPLORATION"],
    ):
        try:
            defer, (uid, userstats) = await asyncio.gather(
                interaction.response.defer(), genshin_app.get_record_card(user.id)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
            return

        try:
            avatar_bytes = await user.display_avatar.read()
            if option == "RECORD":
                fp = draw.draw_record_card(avatar_bytes, uid, userstats)
            elif option == "EXPLORATION":
                fp = draw.draw_exploration_card(avatar_bytes, uid, userstats)
        except Exception as e:
            LOG.ErrorLog(interaction, e)
            sentry_sdk.capture_exception(e)
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            fp.seek(0)
            await interaction.edit_original_response(
                attachments=[discord.File(fp=fp, filename="image.jpeg")]
            )
            fp.close()


class Characters:
    """角色一覽"""

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
                self.add_item(Characters.Dropdown(user, characters[i : i + max_row], i + 1))

    @staticmethod
    async def characters(
        interaction: discord.Interaction, user: Union[discord.User, discord.Member]
    ):
        try:
            defer, characters = await asyncio.gather(
                interaction.response.defer(), genshin_app.get_characters(user.id)
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            view = Characters.DropdownView(user, characters)
            await interaction.edit_original_response(content="請選擇角色：", view=view)


class Notices:
    """原神遊戲內的遊戲與活動公告"""

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
            embed = EmbedTemplate.normal(
                parser.parse_html_content(notice.content), title=notice.title
            )
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

    @staticmethod
    async def notices(interaction: discord.Interaction):
        try:
            defer, notices = await asyncio.gather(
                interaction.response.defer(), genshin_app.get_game_notices()
            )
        except Exception as e:
            await interaction.edit_original_response(embed=EmbedTemplate.error(e))
        else:
            # 將公告分成活動公告、遊戲公告、祈願公告三類
            game: list[genshin.models.Announcement] = []
            event: list[genshin.models.Announcement] = []
            wish: list[genshin.models.Announcement] = []
            for notice in notices:
                if notice.type == 1:
                    if "祈願" in notice.subtitle:
                        wish.append(notice)
                    else:
                        event.append(notice)
                elif notice.type == 2:
                    game.append(notice)

            view = Notices.View()
            if len(game) > 0:
                view.add_item(Notices.Dropdown(game, "遊戲公告："))
            if len(event) > 0:
                view.add_item(Notices.Dropdown(event, "活動公告："))
            if len(wish) > 0:
                view.add_item(Notices.Dropdown(wish, "祈願卡池："))
            await interaction.edit_original_response(view=view)


class GenshinInfo(commands.Cog, name="原神資訊"):
    """斜線指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------------------------------------------
    # 取得使用者即時便箋資訊(樹脂、洞天寶錢、派遣...等)
    @app_commands.command(name="notes即時便箋", description="查詢即時便箋，包含樹脂、洞天寶錢、探索派遣...等")
    @app_commands.rename(shortForm="顯示格式", user="使用者")
    @app_commands.describe(shortForm="選擇顯示完整或簡約格式(省略每日、週本、探索派遣)", user="查詢其他成員的資料，不填寫則查詢自己")
    @app_commands.choices(shortForm=[Choice(name="完整", value=0), Choice(name="簡約", value=1)])
    @SlashCommandLogger
    async def slash_notes(
        self,
        interaction: discord.Interaction,
        shortForm: int = 0,
        user: Optional[discord.User] = None,
    ):
        await RealtimeNotes.notes(interaction, user or interaction.user, shortForm=bool(shortForm))

    # -------------------------------------------------------------
    # 取得使用者旅行者札記
    @app_commands.command(name="diary旅行者札記", description="查詢旅行者札記(原石、摩拉收入)")
    @app_commands.rename(month="月份")
    @app_commands.describe(month="請選擇要查詢的月份")
    @app_commands.choices(
        month=[
            Choice(name="這個月", value=0),
            Choice(name="上個月", value=-1),
            Choice(name="上上個月", value=-2),
        ]
    )
    @SlashCommandLogger
    async def slash_diary(self, interaction: discord.Interaction, month: int):
        month = datetime.datetime.now().month + month
        month = month + 12 if month < 1 else month
        await TravelerDiary.diary(interaction, interaction.user, month)

    # -------------------------------------------------------------
    # 產生遊戲紀錄卡片
    @app_commands.command(name="card紀錄卡片", description="產生原神個人遊戲紀錄卡片")
    @app_commands.rename(option="選項", user="使用者")
    @app_commands.describe(option="選擇要查詢數據總覽或是世界探索度", user="查詢其他成員的資料，不填寫則查詢自己")
    @app_commands.choices(
        option=[
            Choice(name="數據總覽", value="RECORD"),
            Choice(name="世界探索", value="EXPLORATION"),
        ]
    )
    @app_commands.checks.cooldown(1, config.slash_cmd_cooldown)
    @SlashCommandLogger
    async def slash_card(
        self,
        interaction: discord.Interaction,
        option: Literal["RECORD", "EXPLORATION"],
        user: Optional[discord.User] = None,
    ):
        await RecordCard.card(interaction, user or interaction.user, option)

    @slash_card.error
    async def on_slash_card_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                embed=EmbedTemplate.error(f"產生卡片的間隔為{config.slash_cmd_cooldown}秒，請稍後再使用~"),
                ephemeral=True,
            )

    # -------------------------------------------------------------
    # 個人所有角色一覽
    @app_commands.command(name="character角色一覽", description="公開展示我的所有角色")
    @SlashCommandLogger
    async def slash_characters(self, interaction: discord.Interaction):
        await Characters.characters(interaction, interaction.user)

    # -------------------------------------------------------------
    # 遊戲公告與活動公告
    @app_commands.command(name="notices原神公告", description="顯示原神的遊戲公告與活動公告")
    @SlashCommandLogger
    async def slash_notices(self, interaction: discord.Interaction):
        await Notices.notices(interaction)


async def setup(client: commands.Bot):
    await client.add_cog(GenshinInfo(client))

    # -------------------------------------------------------------
    # 下面為Context Menu指令
    @client.tree.context_menu(name="即時便箋")
    @ContextCommandLogger
    async def context_notes(interaction: discord.Interaction, user: discord.User):
        await RealtimeNotes.notes(interaction, user)

    @client.tree.context_menu(name="遊戲紀錄卡片")
    @ContextCommandLogger
    async def context_card(interaction: discord.Interaction, user: discord.User):
        await RecordCard.card(interaction, user, "RECORD")
