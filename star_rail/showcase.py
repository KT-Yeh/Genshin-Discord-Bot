from typing import Any, Callable

import discord
import mihomo
import sentry_sdk
from mihomo import MihomoAPI, StarrailInfoParsed

from data.database import db
from utility import EmbedTemplate, config, emoji, get_app_command_mention
from utility.custom_log import LOG


class Showcase:
    """星穹鐵道角色展示櫃"""

    def __init__(self, uid: int) -> None:
        self.uid = uid
        self.client = MihomoAPI()
        self.data: StarrailInfoParsed
        self.is_cached_data: bool = False

    async def load_data(self) -> None:
        """取得玩家的角色展示櫃資料"""

        cached_data = await db.starrail_showcase.get(self.uid)
        try:
            new_data = await self.client.fetch_user(self.uid)
        except Exception as e:
            if cached_data is None:
                raise e from e
            else:
                self.data = cached_data
                self.is_cached_data = True
        else:
            if cached_data is not None:
                new_data = mihomo.tools.merge_character_data(new_data, cached_data)
            self.data = mihomo.tools.remove_duplicate_character(new_data)
            await db.starrail_showcase.add(self.uid, self.data)

    def get_player_overview_embed(self) -> discord.Embed:
        """取得玩家基本資料的嵌入訊息"""

        player = self.data.player
        player_details = self.data.player_details

        description = (
            f"「{player.signature}」\n"
            f"開拓等級：{player.level}\n"
            f"邂逅角色：{player_details.characters}\n"
            f"達成成就：{player_details.achievements}\n"
            f"模擬宇宙：第 {player_details.simulated_universes} 世界通過\n"
        )
        if (hall := player_details.forgotten_hall) is not None:
            description += "忘卻之庭："
            if hall.memory_of_chaos is not None:
                description += f"{hall.memory_of_chaos} / 10 混沌回憶\n"
            else:
                description += f"{hall.memory} / 15 回憶\n"
        if self.is_cached_data is True:
            description += "(目前無法連接 API，顯示的為快取資料)\n"

        embed = discord.Embed(title=player.name, description=description)
        embed.set_thumbnail(url=self.client.get_icon_url(player.icon))

        if len(self.data.characters) > 0:
            icon = self.data.characters[0].portrait
            embed.set_image(url=self.client.get_icon_url(icon))

        embed.set_footer(text=f"UID：{player.uid}")

        return embed

    def get_character_stat_embed(self, index: int) -> discord.Embed:
        """取得角色屬性資料的嵌入訊息"""

        embed = self.get_default_embed(index)
        embed.title = (embed.title + " 角色面板") if embed.title is not None else "角色面板"

        character = self.data.characters[index]

        # 基本資料
        embed.add_field(
            name="角色資料",
            value=f"星魂：{character.eidolon}\n" + f"等級：Lv. {character.level}\n",
        )
        # 武器
        if character.light_cone is not None:
            light_cone = character.light_cone
            embed.add_field(
                name=f"★{light_cone.rarity} {light_cone.name}",
                value=f"疊影：{light_cone.superimpose} 階\n等級：Lv. {light_cone.level}",
            )
        # 技能
        embed.add_field(
            name="技能",
            value="\n".join(
                f"{trace.type}：Lv. {trace.level}"
                for trace in character.traces
                if trace.type != "秘技"
            ),
            inline=False,
        )
        # 人物屬性
        value = ""
        for stat in character.stats:
            if stat.addition is not None:
                total = int(stat.base) + int(stat.addition)
                value += f"{stat.name}：{total} ({stat.base} +{stat.addition})\n"
            else:
                value += f"{stat.name}：{stat.base}\n"
        embed.add_field(name="屬性面板", value=value, inline=False)

        return embed

    def get_relic_stat_embed(self, index: int) -> discord.Embed:
        """取得角色遺器資料的嵌入訊息"""

        embed = self.get_default_embed(index)
        embed.title = (embed.title + " 聖遺物") if embed.title is not None else "聖遺物"

        character = self.data.characters[index]
        if character.relics is None:
            return embed

        for relic in character.relics:
            # 主詞條
            name = (
                relic.main_property.name.removesuffix("傷害提高").removesuffix("效率").removesuffix("加成")
            )
            value = f"★{relic.rarity}{name}+{relic.main_property.value}\n"
            for prop in relic.sub_property:
                value += f"{prop.name}+{prop.value}\n"

            embed.add_field(name=relic.name, value=value)

        return embed

    def get_default_embed(self, index: int) -> discord.Embed:
        """取得角色的基本嵌入訊息"""

        character = self.data.characters[index]
        color = {
            "物理": 0xC5C5C5,
            "火": 0xF4634E,
            "冰": 0x72C2E6,
            "雷": 0xDC7CF4,
            "風": 0x73D4A4,
            "量子": 0x9590E4,
            "虛數": 0xF7E54B,
        }
        embed = discord.Embed(
            title=f"★{character.rarity} {character.name}",
            color=color.get(character.element),
        )
        embed.set_thumbnail(url=self.client.get_icon_url(character.icon))

        player = self.data.player
        embed.set_author(
            name=f"{player.name} 的角色展示櫃",
            url=f"https://api.mihomo.me/sr_panel/{player.uid}?lang=cht&chara_index={index}",
            icon_url=self.client.get_icon_url(player.icon),
        )
        embed.set_footer(text=f"{player.name}．Lv. {player.level}．UID: {player.uid}")

        return embed


class ShowcaseCharactersDropdown(discord.ui.Select):
    """展示櫃角色下拉選單"""

    showcase: Showcase

    def __init__(self, showcase: Showcase) -> None:
        self.showcase = showcase
        options = [discord.SelectOption(label="玩家資料一覽", value="-1", emoji="📜")]
        for i, character in enumerate(showcase.data.characters):
            if i >= 23:  # Discord 下拉欄位上限
                break
            options.append(
                discord.SelectOption(
                    label=f"★{character.rarity} Lv.{character.level} {character.name}",
                    value=str(i),
                    emoji=emoji.starrail_elements.get(character.element),
                )
            )
        options.append(discord.SelectOption(label="刪除角色快取資料", value="-2", emoji="❌"))
        super().__init__(placeholder="選擇展示櫃角色：", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        index = int(self.values[0])
        if index >= 0:  # 角色資料
            embed = self.showcase.get_character_stat_embed(index)
            await interaction.response.edit_message(
                embed=embed, view=ShowcaseView(self.showcase, index)
            )
        elif index == -1:  # 玩家資料一覽
            embed = self.showcase.get_player_overview_embed()
            await interaction.response.edit_message(
                embed=embed, view=ShowcaseView(self.showcase), attachments=[]
            )
        elif index == -2:  # 刪除快取資料
            # 檢查互動者的 UID 是否符合展示櫃的 UID
            user = await db.users.get(interaction.user.id)
            if user is None or user.uid_starrail != self.showcase.uid:
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
                await db.starrail_showcase.remove(self.showcase.uid)
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


class ShowcaseView(discord.ui.View):
    """角色展示櫃View，顯示角色面板、聖遺物詞條按鈕，以及角色下拉選單"""

    def __init__(self, showcase: Showcase, character_index: int | None = None):
        super().__init__(timeout=config.discord_view_long_timeout)
        if character_index is not None:
            self.add_item(ShowcaseButton("面板", showcase.get_character_stat_embed, character_index))
            self.add_item(ShowcaseButton("遺器", showcase.get_relic_stat_embed, character_index))

        if len(showcase.data.characters) > 0:
            self.add_item(ShowcaseCharactersDropdown(showcase))


# -------------------------------------------------------------------
# 下面為Discord指令呼叫


async def starrail_showcase(
    interaction: discord.Interaction,
    user: discord.User | discord.Member,
    uid: int | None = None,
):
    await interaction.response.defer()
    uid = uid or (_user.uid_starrail if (_user := await db.users.get(user.id)) else None)
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
            embed = EmbedTemplate.error(e, title=f"UID：{uid}")
            await interaction.edit_original_response(embed=embed)
