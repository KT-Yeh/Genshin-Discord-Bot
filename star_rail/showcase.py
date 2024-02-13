import io
import json
from typing import Tuple

import discord
from honkairail.src.tools.modalV2 import StarRailApiDataV2
from hsrcard.hsr import HonkaiCard
from mihomo import MihomoAPI, StarrailInfoParsed
from mihomo import tools as mihomo_tools

from database import Database, StarrailShowcase


class Showcase:
    """星穹鐵道角色展示櫃"""

    def __init__(self, uid: int) -> None:
        self.uid = uid
        self.client = MihomoAPI()
        self.data: StarrailInfoParsed
        self.is_cached_data: bool = False

    async def load_data(self) -> None:
        """取得玩家的角色展示櫃資料"""

        # 從資料庫取得舊資料作為快取資料
        srshowcase = await Database.select_one(
            StarrailShowcase, StarrailShowcase.uid.is_(self.uid)
        )
        cached_data: StarrailInfoParsed | None = None
        if srshowcase:
            cached_data = srshowcase.data
        try:
            new_data = await self.client.fetch_user(self.uid)
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

        description = (
            f"「{player.signature}」\n"
            f"開拓等級：{player.level}\n"
            f"邂逅角色：{player.characters}\n"
            f"達成成就：{player.achievements}\n"
        )

        if self.is_cached_data is True:
            description += "(目前無法連接 API，顯示的為快取資料)\n"

        embed = discord.Embed(title=player.name, description=description)
        embed.set_thumbnail(url=self.client.get_icon_url(player.avatar.icon))

        if len(self.data.characters) > 0:
            icon = self.data.characters[0].portrait
            embed.set_image(url=self.client.get_icon_url(icon))

        embed.set_footer(text=f"UID：{player.uid}")

        return embed

    async def get_character_card_embed_file(
        self, index: int
    ) -> Tuple[discord.Embed, discord.File]:
        """取得角色的卡片資料"""

        embed = self.get_default_embed(index)
        embed.set_thumbnail(url=None)

        data_dict = self.data.dict(by_alias=True)
        data_dict["player"]["space_info"] = {}
        data_hsrcard = StarRailApiDataV2.parse_raw(json.dumps(data_dict, ensure_ascii=False))

        async with HonkaiCard(lang="cht") as card_creater:
            result = await card_creater.creat(self.uid, data_hsrcard, index)
            image = result.card[0].card

        fp = io.BytesIO()
        image = image.convert("RGB")
        image.save(fp, "jpeg", optimize=True, quality=90)
        fp.seek(0)

        embed.set_image(url="attachment://image.jpeg")
        file = discord.File(fp, "image.jpeg")
        return (embed, file)

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
                f"{trace.type_text}：Lv. {trace.level}"
                for trace in character.traces
                if trace.type_text != "" and trace.type_text != "秘技"
            ),
            inline=False,
        )
        # 人物屬性
        attr_dict = {
            "生命值": [0.0, 0.0],
            "攻擊力": [0.0, 0.0],
            "防禦力": [0.0, 0.0],
            "速度": [0.0, 0.0],
            "暴擊率": [5.0, 0.0],
            "暴擊傷害": [50.0, 0.0],
            "能量恢復效率": [100.0, 0.0],
        }
        for stat in character.attributes:
            if stat.name not in attr_dict:
                attr_dict[stat.name] = [0.0, 0.0]
            attr_dict[stat.name][0] += stat.value * 100 if stat.is_percent else stat.value

        for stat in character.additions:
            if stat.name not in attr_dict:
                attr_dict[stat.name] = [0.0, 0.0]
            attr_dict[stat.name][1] += stat.value * 100 if stat.is_percent else stat.value

        # 將傷害提高應用到所有屬性的傷害提高
        if "傷害提高" in attr_dict:
            v = attr_dict["傷害提高"][0] + attr_dict["傷害提高"][1]
            del attr_dict["傷害提高"]
            for key in attr_dict:
                if "傷害提高" in key:
                    attr_dict[key][1] += v

        value = ""
        for k, v in attr_dict.items():
            value += f"{k}：{round(v[0] + v[1], 1)}\n"
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
                relic.main_affix.name.removesuffix("傷害提高")
                .removesuffix("效率")
                .removesuffix("加成")
            )
            value = f"★{relic.rarity}{name}+{relic.main_affix.displayed_value}\n"
            for prop in relic.sub_affixes:
                value += f"{prop.name}+{prop.displayed_value}\n"

            embed.add_field(name=relic.name, value=value)

        return embed

    def get_relic_score_embed(self, index: int) -> discord.Embed:
        """取得角色遺器詞條數的嵌入訊息"""

        embed = self.get_default_embed(index)
        embed.title = (embed.title + "詞條數") if embed.title is not None else "詞條數"

        character = self.data.characters[index]
        relics = character.relics
        if relics is None:
            return embed

        substat_sum: dict[str, float] = {  # 副詞條數量統計
            "攻擊力": 0.0,
            "生命值": 0.0,
            "防禦力": 0.0,
            "速度": 0.0,
            "暴擊率": 0.0,
            "暴擊傷害": 0.0,
            "效果命中": 0.0,
            "效果抗性": 0.0,
            "擊破特攻": 0.0,
        }
        crit_value: float = 0.0  # 雙爆分

        base_hp = float(
            next(s for s in character.attributes if s.name == "生命值").value
        )  # 生命白值
        base_atk = float(
            next(s for s in character.attributes if s.name == "攻擊力").value
        )  # 攻擊白值
        base_def = float(
            next(s for s in character.attributes if s.name == "防禦力").value
        )  # 防禦白值

        for relic in relics:
            main = relic.main_affix
            if main.name == "暴擊率":
                crit_value += float(main.value) * 100 * 2
            if main.name == "暴擊傷害":
                crit_value += float(main.value) * 100
            for prop in relic.sub_affixes:
                v = prop.displayed_value
                if v is None:
                    continue
                match prop.name:
                    case "生命值":
                        p = float(v.removesuffix("%")) if v.endswith("%") else float(v) / base_hp
                        substat_sum["生命值"] += p / 3.89
                    case "攻擊力":
                        p = float(v.removesuffix("%")) if v.endswith("%") else float(v) / base_atk
                        substat_sum["攻擊力"] += p / 3.89
                    case "防禦力":
                        p = float(v.removesuffix("%")) if v.endswith("%") else float(v) / base_def
                        substat_sum["防禦力"] += p / 4.86
                    case "速度":
                        substat_sum["速度"] += float(v) / 2.3
                    case "暴擊率":
                        p = float(v.removesuffix("%"))
                        crit_value += p * 2.0
                        substat_sum["暴擊率"] += p / 2.92
                    case "暴擊傷害":
                        p = float(v.removesuffix("%"))
                        crit_value += p
                        substat_sum["暴擊傷害"] += p / 5.83
                    case "效果命中":
                        substat_sum["效果命中"] += float(v.removesuffix("%")) / 3.89
                    case "效果抗性":
                        substat_sum["效果抗性"] += float(v.removesuffix("%")) / 3.89
                    case "擊破特攻":
                        substat_sum["擊破特攻"] += float(v.removesuffix("%")) / 5.83
        embed.add_field(
            name="詞條數",
            value="\n".join(
                [f"{k.ljust(4, '　')}：{round(v, 1)}" for k, v in substat_sum.items() if v > 0]
            ),
        )

        # 詞條組合統計
        def sum_substat(name: str, *args: str) -> str:
            total = 0.0
            for arg in args:
                total += substat_sum[arg]
            # 要超過 (4 * 詞條種類數量) 條以上才會顯示
            return f"{name.ljust(4, '　')}：{round(total, 1)}\n" if total > 4 * len(args) else ""

        embed_value = f"雙暴 {round(crit_value)} 分\n"
        embed_value += sum_substat("攻雙暴", "攻擊力", "暴擊率", "暴擊傷害")
        embed_value += sum_substat("攻速雙暴", "攻擊力", "速度", "暴擊率", "暴擊傷害")
        embed_value += sum_substat("攻命雙暴", "攻擊力", "效果命中", "暴擊率", "暴擊傷害")
        embed_value += sum_substat("生速雙暴", "生命值", "速度", "暴擊率", "暴擊傷害")
        embed_value += sum_substat("生攻速暴", "生命值", "攻擊力", "速度", "暴擊率", "暴擊傷害")
        embed_value += sum_substat("生速抗", "生命值", "速度", "效果抗性")
        embed_value += sum_substat("生防速", "生命值", "防禦力", "速度")
        embed_value += sum_substat("防速抗", "防禦力", "速度", "效果抗性")
        embed_value += sum_substat("防速命抗", "防禦力", "速度", "效果命中", "效果抗性")

        embed.add_field(name="總詞條統計", value=embed_value)

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
            color=color.get(character.element.name),
        )
        embed.set_thumbnail(url=self.client.get_icon_url(character.icon))

        player = self.data.player
        embed.set_author(
            name=f"{player.name} 的角色展示櫃",
            icon_url=self.client.get_icon_url(player.avatar.icon),
        )
        embed.set_footer(text=f"{player.name}．Lv. {player.level}．UID: {player.uid}")

        return embed
