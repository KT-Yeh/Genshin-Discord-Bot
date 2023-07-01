import io
from datetime import datetime
from typing import Any

import discord
import enkanetwork

from database import Database, GenshinShowcase
from utility import emoji

from .api import EnkaAPI
from .enka_card import generate_image
from .request import fetch_enka_data

enka_assets = enkanetwork.Assets(lang=enkanetwork.Language.CHT)


class Showcase:
    """使用者的角色展示櫃

    Attributes
    -----
    raw_data: `Dict[str, Any] | None`
        從 Enka API 取得的原生 JSON 資料
    data: `enkanetwork.EnkaNetworkResponse`
        經由 EnkaNetwork.py 解析 raw_data 後的資料
    uid: `int`
        使用者的原神 UID
    is_cached_data: `bool`
        目前的展示櫃資料是否為快取資料
    api_error_msg: `str | None`
        向 API 請求發生錯誤時，此錯誤的訊息內容
    url: `str`
        玩家在 enka network 網站上的 URL
    image_buffers: `List[BytesIO | None]`
        玩家的角色展示櫃圖片快取
    """

    def __init__(self, uid: int) -> None:
        self.raw_data: dict[str, Any] | None = None
        self.data: enkanetwork.EnkaNetworkResponse
        self.uid: int = uid
        self.is_cached_data = False
        self.api_error_msg: str | None = None
        self.url: str = EnkaAPI.get_user_url(uid)
        self.image_buffers: list[io.BytesIO | None] = [None] * 25

    async def load_data(self) -> None:
        """取得玩家的角色展示櫃資料"""
        # 從資料庫取得快取資料
        gshowcase = await Database.select_one(GenshinShowcase, GenshinShowcase.uid.is_(self.uid))
        if gshowcase is not None:
            self.raw_data = gshowcase.data

        if self.raw_data is None:  # 新的使用者
            self.raw_data = await fetch_enka_data(self.uid)
        else:  # 舊有的使用者
            # 為了減少無效的重複請求，檢查快取時間戳是否有效，若超過期限則從API取得資料
            refresh_timestamp = self.raw_data.get("timestamp", 0) + self.raw_data.get("ttl", 0)
            if datetime.now().timestamp() > refresh_timestamp:
                try:
                    self.raw_data = await fetch_enka_data(self.uid, self.raw_data)
                except Exception as e:
                    # 發生錯誤時，標記目前資料為快取資料
                    self.is_cached_data = True
                    self.api_error_msg = str(e)

        # 當有從 API 取得資料時 (非快取)，則存入資料庫
        if self.is_cached_data is False:
            gshowcase = GenshinShowcase(self.uid, self.raw_data)
            await Database.insert_or_replace(gshowcase)

        self.data = enkanetwork.EnkaNetworkResponse.parse_obj(self.raw_data)

    def get_player_overview_embed(self) -> discord.Embed:
        """取得玩家基本資料的嵌入訊息"""
        player = self.data.player
        if self.raw_data is None or player is None:
            raise Exception("玩家資料不存在")
        embed = discord.Embed(
            title=player.nickname,
            description=f"「{player.signature}」\n"
            f"冒險等階：{player.level}\n"
            f"世界等級：{player.world_level}\n"
            f"成就總數：{player.achievement}\n"
            f"深境螺旋：{player.abyss_floor}-{player.abyss_room}\n"
            f"下次可刷新時間：<t:{self.raw_data.get('timestamp', 0) + self.raw_data.get('ttl', 0)}:R>\n"
            + (f"({self.api_error_msg}，顯示的為快取資料)" if self.is_cached_data is True else ""),
        )
        if player.avatar and player.avatar.icon:
            embed.set_thumbnail(url=player.avatar.icon.url)

        if player.namecard.icon and player.namecard.banner:
            embed.set_image(url=player.namecard.banner.url)

        embed.set_footer(text=f"UID: {self.uid}")
        return embed

    def get_character_stat_embed(self, index: int) -> discord.Embed:
        """取得角色面板的嵌入訊息"""
        embed = self.get_default_embed(index)
        embed.title = (embed.title + " 角色面板") if embed.title is not None else "角色面板"
        if self.data.characters is None:
            return embed

        character = self.data.characters[index]

        # 基本資料
        skill_string = (  # 天賦等級
            f"{character.skills[0].level}/{character.skills[1].level}/{character.skills[-1].level}"
            if len(character.skills) >= 3
            else "?/?/?"
        )
        embed.add_field(
            name="角色資料",
            value=f"命座：{character.constellations_unlocked}\n"
            f"等級：Lv. {character.level}\n"
            f"天賦：{skill_string}\n"
            f"好感：Lv. {character.friendship_level}",
        )
        # 武器
        weapon_list = [
            e for e in character.equipments if e.type == enkanetwork.EquipmentsType.WEAPON
        ]
        if len(weapon_list) > 0:
            weapon = weapon_list[0]
            embed.add_field(
                name=f"★{weapon.detail.rarity} {weapon.detail.name}",
                value=f"精煉：{weapon.refinement} 階\n"
                f"等級：Lv. {weapon.level}\n"
                f"{self._get_statprop_sentence(weapon.detail.mainstats) if weapon.detail.mainstats else ''}\n"
                f"{self._get_statprop_sentence(weapon.detail.substats[0]) if len(weapon.detail.substats) > 0 else ''}",
            )
        # 人物面板
        stats = character.stats
        substat: str = "\n".join(
            [
                self._get_character_fightprop_sentence(stat_name, stat)
                for (stat_name, stat) in [
                    ("FIGHT_PROP_CRITICAL", stats.FIGHT_PROP_CRITICAL),
                    ("FIGHT_PROP_CRITICAL_HURT", stats.FIGHT_PROP_CRITICAL_HURT),
                    ("FIGHT_PROP_ELEMENT_MASTERY", stats.FIGHT_PROP_ELEMENT_MASTERY),
                    ("FIGHT_PROP_HEAL_ADD", stats.FIGHT_PROP_HEAL_ADD),
                    ("FIGHT_PROP_CHARGE_EFFICIENCY", stats.FIGHT_PROP_CHARGE_EFFICIENCY),
                    ("FIGHT_PROP_PHYSICAL_ADD_HURT", stats.FIGHT_PROP_PHYSICAL_ADD_HURT),
                    ("FIGHT_PROP_FIRE_ADD_HURT", stats.FIGHT_PROP_FIRE_ADD_HURT),
                    ("FIGHT_PROP_ELEC_ADD_HURT", stats.FIGHT_PROP_ELEC_ADD_HURT),
                    ("FIGHT_PROP_WATER_ADD_HURT", stats.FIGHT_PROP_WATER_ADD_HURT),
                    ("FIGHT_PROP_GRASS_ADD_HURT", stats.FIGHT_PROP_GRASS_ADD_HURT),
                    ("FIGHT_PROP_WIND_ADD_HURT", stats.FIGHT_PROP_WIND_ADD_HURT),
                    ("FIGHT_PROP_ROCK_ADD_HURT", stats.FIGHT_PROP_ROCK_ADD_HURT),
                    ("FIGHT_PROP_ICE_ADD_HURT", stats.FIGHT_PROP_ICE_ADD_HURT),
                ]
                if stat.value > 0
            ]
        )
        _hp = [
            round(stats.FIGHT_PROP_MAX_HP.value),
            round(stats.BASE_HP.value),
            round(stats.FIGHT_PROP_MAX_HP.value - stats.BASE_HP.value),
        ]
        _atk = [
            round(stats.FIGHT_PROP_CUR_ATTACK.value),
            round(stats.FIGHT_PROP_BASE_ATTACK.value),
            round(stats.FIGHT_PROP_CUR_ATTACK.value - stats.FIGHT_PROP_BASE_ATTACK.value),
        ]
        _def = [
            round(stats.FIGHT_PROP_CUR_DEFENSE.value),
            round(stats.FIGHT_PROP_BASE_DEFENSE.value),
            round(stats.FIGHT_PROP_CUR_DEFENSE.value - stats.FIGHT_PROP_BASE_DEFENSE.value),
        ]
        _emoji = {
            "HP": emoji.fightprop.get("FIGHT_PROP_HP", ""),
            "ATK": emoji.fightprop.get("FIGHT_PROP_ATTACK", ""),
            "DEF": emoji.fightprop.get("FIGHT_PROP_DEFENSE", ""),
        }
        embed.add_field(
            name="屬性面板",
            value=(
                f"{_emoji['HP']}生命值：{_hp[0]} ({_hp[1]} +{_hp[2]})\n"
                f"{_emoji['ATK']}攻擊力：{_atk[0]} ({_atk[1]} +{_atk[2]})\n"
                f"{_emoji['DEF']}防禦力：{_def[0]} ({_def[1]} +{_def[2]})\n"
                f"{substat}"
            ),
            inline=False,
        )
        return embed

    def get_artifact_stat_embed(self, index: int) -> discord.Embed:
        """取得角色聖遺物詞條數的嵌入訊息"""
        embed = self.get_default_embed(index)
        embed.title = (embed.title + " 聖遺物") if embed.title is not None else "聖遺物"

        if self.data.characters is None:
            return embed

        pos_name_map = {
            "EQUIP_BRACER": "花",
            "EQUIP_NECKLACE": "羽",
            "EQUIP_SHOES": "沙",
            "EQUIP_RING": "杯",
            "EQUIP_DRESS": "冠",
        }
        substat_sum: dict[str, float] = dict()  # 副詞條數量統計
        crit_value: float = 0.0  # 雙爆分

        character = self.data.characters[index]
        for equip in character.equipments:
            if equip.type != enkanetwork.EquipmentsType.ARTIFACT:
                continue

            # 主詞條屬性
            if (mainstats := equip.detail.mainstats) is None:
                continue
            embed_value = f"{self._get_statprop_sentence(mainstats)}\n"
            crit_value += (
                mainstats.value * 2
                if mainstats.prop_id == "FIGHT_PROP_CRITICAL"
                else mainstats.value
                if mainstats.prop_id == "FIGHT_PROP_CRITICAL_HURT"
                else 0
            )

            # 副詞條屬性
            for substat in equip.detail.substats:
                # prop: str = substat["appendPropId"]  # 副詞條屬性名字，例：FIGHT_PROP_ATTACK_PERCENT
                # value: Union[int, float] = substat["statValue"]  # 副詞條數值
                substat_sum[substat.prop_id] = substat_sum.get(substat.prop_id, 0) + substat.value

            # 聖遺物部位
            pos_name = pos_name_map.get(equip.detail.artifact_type.value, "未知")

            _artifact_emoji = emoji.artifact_type.get(pos_name, pos_name + "：")
            _artifact_set_name = equip.detail.artifact_name_set

            # 只將沙、杯、冠的聖遺物顯示在嵌入訊息中
            if pos_name not in ["花", "羽"]:
                embed.add_field(
                    name=f"{_artifact_emoji}{_artifact_set_name}",
                    value=embed_value,
                    inline=False,
                )

        # 將小詞條換算成大詞條
        if "FIGHT_PROP_HP" in substat_sum.keys():  # 將小生命換算成生命%詞條
            substat_sum["FIGHT_PROP_HP_PERCENT"] = substat_sum.get("FIGHT_PROP_HP_PERCENT", 0) + (
                substat_sum["FIGHT_PROP_HP"] * 100 / character.stats.BASE_HP.value
            )
        if "FIGHT_PROP_ATTACK" in substat_sum.keys():  # 將小攻擊換算成攻擊%詞條
            substat_sum["FIGHT_PROP_ATTACK_PERCENT"] = substat_sum.get(
                "FIGHT_PROP_ATTACK_PERCENT", 0
            ) + (
                substat_sum["FIGHT_PROP_ATTACK"]
                * 100
                / character.stats.FIGHT_PROP_BASE_ATTACK.value
            )
        if "FIGHT_PROP_DEFENSE" in substat_sum.keys():  # 將小防禦換算成防禦%詞條
            substat_sum["FIGHT_PROP_DEFENSE_PERCENT"] = substat_sum.get(
                "FIGHT_PROP_DEFENSE_PERCENT", 0
            ) + (
                substat_sum["FIGHT_PROP_DEFENSE"]
                * 100
                / character.stats.FIGHT_PROP_BASE_DEFENSE.value
            )

        # 副詞條數量統計
        def substatSummary(prop: str, name: str, base: float) -> str:
            return (
                f"{emoji.fightprop.get(prop, '')}{name}：{round(value / base, 1)}\n"
                if (value := substat_sum.get(prop)) is not None
                else ""
            )

        embed_value = ""
        embed_value += substatSummary("FIGHT_PROP_ATTACK_PERCENT", "攻擊力％", 5.0)
        embed_value += substatSummary("FIGHT_PROP_HP_PERCENT", "生命值％", 5.0)
        embed_value += substatSummary("FIGHT_PROP_DEFENSE_PERCENT", "防禦力％", 6.2)
        embed_value += substatSummary("FIGHT_PROP_CHARGE_EFFICIENCY", "元素充能", 5.5)
        embed_value += substatSummary("FIGHT_PROP_ELEMENT_MASTERY", "元素精通", 20)
        embed_value += substatSummary("FIGHT_PROP_CRITICAL", "暴擊率　", 3.3)
        embed_value += substatSummary("FIGHT_PROP_CRITICAL_HURT", "暴擊傷害", 6.6)
        if embed_value != "":
            crit_value += substat_sum.get("FIGHT_PROP_CRITICAL", 0) * 2 + substat_sum.get(
                "FIGHT_PROP_CRITICAL_HURT", 0
            )
            embed.add_field(
                name="詞條數" + (f" (雙爆{round(crit_value)})" if crit_value > 100 else ""),
                value=embed_value,
            )

        return embed

    async def get_image(self, index: int) -> io.BytesIO | None:
        """取得角色展示櫃圖片"""
        if self.data.characters is None:
            return None

        if (image_buffer := self.image_buffers[index]) is not None:
            image = image_buffer
            image.seek(0)
        else:
            image = await generate_image(
                self.data,
                self.data.characters[index],
                enkanetwork.Language.CHT,
                save_locally=False,
            )
            self.image_buffers[index] = image
        return image

    def get_default_embed(self, index: int) -> discord.Embed:
        character = self.data.player.characters_preview[index]  # type: ignore
        color = {
            enkanetwork.ElementType.Pyro: 0xFB4120,
            enkanetwork.ElementType.Electro: 0xBF73E7,
            enkanetwork.ElementType.Hydro: 0x15B1FF,
            enkanetwork.ElementType.Cryo: 0x70DAF1,
            enkanetwork.ElementType.Dendro: 0xA0CA22,
            enkanetwork.ElementType.Anemo: 0x5CD4AC,
            enkanetwork.ElementType.Geo: 0xFAB632,
        }
        _assets_character = enka_assets.character(character.id)
        embed = discord.Embed(
            title=f"★{_assets_character.rarity if _assets_character else '?'} {character.name}",
            color=color.get(character.element),
        )
        if character.icon:
            embed.set_thumbnail(url=character.icon.url)

        if (player := self.data.player) is not None:
            embed.set_author(
                name=f"{player.nickname} 的角色展示櫃",
                url=self.url,
                icon_url=player.avatar.icon.url if player.avatar and player.avatar.icon else None,
            )
            embed.set_footer(text=f"{player.nickname}．Lv. {player.level}．UID: {self.uid}")

        if self.data.characters is None:
            embed.description = "請在您遊戲中的角色展示櫃中打開「顯示角色詳情」來查看更詳細的角色資料"

        return embed

    def _get_character_fightprop_sentence(
        self, stat_name: str, stat: enkanetwork.Stats | enkanetwork.StatsPercentage
    ) -> str:
        """範例：暴擊傷害：112.2%"""
        emoji_str = emoji.fightprop.get(stat_name, "")
        prop_name = enka_assets.get_hash_map(stat_name)
        if isinstance(stat, enkanetwork.StatsPercentage):
            return f"{emoji_str}{prop_name}：{stat.to_percentage_symbol()}"
        return f"{emoji_str}{prop_name}：{stat.to_rounded()}"

    def _get_statprop_sentence(self, equip_stat: enkanetwork.EquipmentsStats) -> str:
        """範例：暴擊率+22.1%"""
        emoji_str = emoji.fightprop.get(equip_stat.prop_id, "")
        return f"{emoji_str}{equip_stat.name}+{equip_stat.value}" + (
            "%" if equip_stat.type == enkanetwork.DigitType.PERCENT else ""
        )
