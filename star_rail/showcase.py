import discord
from mihomo import MihomoAPI, StarrailInfoParsedV1
from mihomo import tools as mihomo_tools

from database import Database, StarrailShowcase


class Showcase:
    """星穹鐵道角色展示櫃"""

    def __init__(self, uid: int) -> None:
        self.uid = uid
        self.client = MihomoAPI()
        self.data: StarrailInfoParsedV1
        self.is_cached_data: bool = False

    async def load_data(self) -> None:
        """取得玩家的角色展示櫃資料"""

        # 從資料庫取得舊資料作為快取資料
        srshowcase = await Database.select_one(
            StarrailShowcase, StarrailShowcase.uid.is_(self.uid)
        )
        cached_data: StarrailInfoParsedV1 | None = None
        if srshowcase:
            cached_data = srshowcase.data
        try:
            new_data = await self.client.fetch_user_v1(self.uid)
        except Exception as e:
            # 無法從 API 取得時，改用資料庫資料，若兩者都沒有則拋出錯誤
            if cached_data is None:
                raise e from e
            else:
                self.data = cached_data
                self.is_cached_data = True
        else:
            if cached_data is not None:
                new_data = mihomo_tools.merge_character_data(new_data, cached_data)
            self.data = mihomo_tools.remove_duplicate_character(new_data)
            await Database.insert_or_replace(StarrailShowcase(self.uid, self.data))

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
