import asyncio
from typing import Any, Callable, Optional, Union

import discord
import enkanetwork
import sentry_sdk
from discord import app_commands
from discord.ext import commands

from data.database import db
from enka_network import Showcase, enka_assets
from utility import EmbedTemplate, config, emoji, get_app_command_mention
from utility.custom_log import LOG, ContextCommandLogger, SlashCommandLogger


class ShowcaseCharactersDropdown(discord.ui.Select):
    """展示櫃角色下拉選單"""

    showcase: Showcase

    def __init__(self, showcase: Showcase) -> None:
        self.showcase = showcase
        options = [discord.SelectOption(label="玩家資料一覽", value="-1", emoji="📜")]
        for i, character in enumerate(showcase.data.player.characters_preview):  # type: ignore
            element = {
                enkanetwork.ElementType.Pyro: "pyro",
                enkanetwork.ElementType.Electro: "electro",
                enkanetwork.ElementType.Hydro: "hydro",
                enkanetwork.ElementType.Cryo: "cryo",
                enkanetwork.ElementType.Dendro: "dendro",
                enkanetwork.ElementType.Anemo: "anemo",
                enkanetwork.ElementType.Geo: "geo",
            }.get(character.element, "")
            _assets_character = enka_assets.character(character.id)
            _rarity = _assets_character.rarity if _assets_character else "?"

            options.append(
                discord.SelectOption(
                    label=f"★{_rarity} Lv.{character.level} {character.name}",
                    value=str(i),
                    emoji=emoji.elements.get(element),
                )
            )
        options.append(discord.SelectOption(label="刪除角色快取資料", value="-2", emoji="❌"))
        super().__init__(placeholder="選擇展示櫃角色：", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        index = int(self.values[0])
        if index >= 0:  # 角色資料
            await GenerateImageButton.handle_image_response(interaction, self.showcase, index)
            await interaction.edit_original_response(view=ShowcaseView(self.showcase, index))
        elif index == -1:  # 玩家資料一覽
            embed = self.showcase.get_player_overview_embed()
            await interaction.response.edit_message(
                embed=embed, view=ShowcaseView(self.showcase), attachments=[]
            )
        elif index == -2:  # 刪除快取資料
            # 檢查互動者的 UID 是否符合展示櫃的 UID
            user = await db.users.get(interaction.user.id)
            if user is None or user.uid != self.showcase.uid:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("非此UID本人，無法刪除資料"), ephemeral=True
                )
            elif len(user.cookie) == 0:
                await interaction.response.send_message(
                    embed=EmbedTemplate.error("未設定Cookie，無法驗證此UID本人，無法刪除資料"),
                    ephemeral=True,
                )
            else:
                embed = self.showcase.get_player_overview_embed()
                await db.showcase.remove(self.showcase.uid)
                await interaction.response.edit_message(embed=embed, view=None, attachments=[])


class ShowcaseButton(discord.ui.Button):
    """角色展示櫃按鈕"""

    def __init__(self, label: str, function: Callable[..., discord.Embed], *args, **kwargs):
        super().__init__(style=discord.ButtonStyle.primary, label=label)
        self.callback_func = function
        self.callback_args = args
        self.callback_kwargs = kwargs

    async def callback(self, interaction: discord.Interaction) -> Any:
        embed = self.callback_func(*self.callback_args, **self.callback_kwargs)
        await interaction.response.edit_message(embed=embed, attachments=[])


class GenerateImageButton(discord.ui.Button):
    """產生圖片按鈕"""

    def __init__(self, showcase: Showcase, character_index: int):
        super().__init__(style=discord.ButtonStyle.primary, label="圖片")
        self.showcase = showcase
        self.character_index = character_index

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.handle_image_response(interaction, self.showcase, self.character_index)

    @classmethod
    async def handle_image_response(
        cls, interaction: discord.Interaction, showcase: Showcase, character_index: int
    ) -> None:
        """產生角色圖片，處理 discord interaction 回覆 embed 給使用者"""
        embed = showcase.get_default_embed(character_index)
        _, image = await asyncio.gather(
            interaction.response.edit_message(embed=embed, attachments=[]),
            showcase.get_image(character_index),
        )
        if image is not None:
            embed.set_thumbnail(url=None)
            embed.set_image(url="attachment://image.jpeg")
            await interaction.edit_original_response(
                embed=embed, attachments=[discord.File(image, "image.jpeg")]
            )


class ShowcaseView(discord.ui.View):
    """角色展示櫃View，顯示角色面板圖、聖遺物詞條按鈕，以及角色下拉選單"""

    def __init__(self, showcase: Showcase, character_index: Optional[int] = None):
        super().__init__(timeout=config.discord_view_long_timeout)
        if character_index is not None:
            self.add_item(GenerateImageButton(showcase, character_index))
            self.add_item(ShowcaseButton("面板", showcase.get_character_stat_embed, character_index))
            self.add_item(ShowcaseButton("詞條", showcase.get_artifact_stat_embed, character_index))

        if showcase.data.player.characters_preview:  # type: ignore
            self.add_item(ShowcaseCharactersDropdown(showcase))


# -------------------------------------------------------------------
# 下面為Discord指令呼叫


async def showcase(
    interaction: discord.Interaction,
    user: Union[discord.User, discord.Member],
    uid: Optional[int] = None,
):
    await interaction.response.defer()
    uid = uid or (_user.uid if (_user := await db.users.get(user.id)) else None)
    if uid is None:
        await interaction.edit_original_response(
            embed=EmbedTemplate.error(
                f"請先使用 {get_app_command_mention('uid設定')}，或是直接在指令uid參數中輸入欲查詢的UID",
                title="找不到角色UID",
            )
        )
    elif len(str(uid)) != 9 or str(uid)[0] not in ["1", "2", "5", "6", "7", "8", "9"]:
        await interaction.edit_original_response(embed=EmbedTemplate.error("輸入的UID格式錯誤"))
    else:
        showcase = Showcase(uid)
        try:
            await showcase.load_data()
            view = ShowcaseView(showcase)
            embed = showcase.get_player_overview_embed()
            await interaction.edit_original_response(embed=embed, view=view)
        except Exception as e:
            LOG.ErrorLog(interaction, e)
            sentry_sdk.capture_exception(e)

            embed = EmbedTemplate.error(
                str(e) + f"\n你可以點擊 [連結]({showcase.url}) 查看網站狀態", title=f"UID：{uid}"
            )
            await interaction.edit_original_response(embed=embed)


class GenshinShowcase(commands.Cog, name="原神展示櫃"):
    """斜線指令"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 角色展示櫃
    @app_commands.command(name="showcase角色展示櫃", description="查詢指定UID玩家的公開角色展示櫃")
    @app_commands.rename(user="使用者")
    @app_commands.describe(uid="欲查詢的玩家UID，若小幫手已保存資料的話查自己不需要填本欄位", user="查詢其他成員的資料，不填寫則查詢自己")
    @SlashCommandLogger
    async def slash_showcase(
        self,
        interaction: discord.Interaction,
        uid: Optional[int] = None,
        user: Optional[discord.User] = None,
    ):
        await showcase(interaction, user or interaction.user, uid)


async def setup(client: commands.Bot):
    # 更新 Enka 素材資料
    enka = enkanetwork.EnkaNetworkAPI()
    async with enka:
        await enka.update_assets()
    enkanetwork.Assets(lang=enkanetwork.Language.CHT)

    await client.add_cog(GenshinShowcase(client))

    # ---------------------------------------------------------------
    # 下面為Context Menu指令
    @client.tree.context_menu(name="角色展示櫃")
    @ContextCommandLogger
    async def context_showcase(interaction: discord.Interaction, user: discord.User):
        await showcase(interaction, user, None)
