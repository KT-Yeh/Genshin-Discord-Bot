from typing import Callable, Type

import discord

from utility import EmbedTemplate, emoji

from .api import API
from .models import Achievement, Character, Constellation, Food, Material, Talent, Weapon
from .models.artifacts import Artifact, PartDetail
from .models.tcg_cards import ActionCard, CharacterCard, DiceCost, Summon


def parse(model) -> discord.Embed:
    """傳入 genshin-db model的物件，自動解析並傳回 discord.Embed"""
    # 此工廠字典須隨著底下 parser 增加與之對應
    _map: dict[Type, Callable] = {
        CharacterCard: TCGCardParser.parse_character_card,
        ActionCard: TCGCardParser.parse_action_card,
        Summon: TCGCardParser.parse_summon,
        Achievement: AchievemntParser.parse_achievement,
        Artifact: EquipmentParser.parse_artifact,
        PartDetail: EquipmentParser.parse_artifact_part,
        Weapon: EquipmentParser.parse_weapon,
        Character: CharacterParser.parse_character,
        Talent: CharacterParser.parse_talent,
        Constellation: CharacterParser.parse_constellation,
        Food: MaterialParser.parse_food,
        Material: MaterialParser.parse_material,
    }
    parser = _map.get(type(model))
    if parser is not None:
        return parser(model)
    else:
        return EmbedTemplate.error("發生錯誤，無法解析資料")


class TCGCardParser:
    """七聖召喚"""

    @classmethod
    def _parse_costs(cls, costs: list[DiceCost]) -> str:
        """解析骰子花費"""
        if len(costs) == 0:
            return "無"
        cost_texts: list[str] = []
        for cost in costs:
            if _emoji := emoji.tcg_dice_cost_elements.get(cost.element.name):
                _text = _emoji
            else:
                _text = str(cost.element)
            cost_texts.append(f"{_text} ({cost.amount})")
        return " / ".join(cost_texts)

    @classmethod
    def parse_character_card(cls, card: CharacterCard) -> discord.Embed:
        """解析角色牌內容，傳回 discord.Embed"""
        embed = EmbedTemplate.normal(card.story_text or " ", title=card.name)
        embed.set_image(url=card.image_url)
        for talent in card.talents:
            _value = "花費：" + cls._parse_costs(talent.costs) + "\n"
            _value += talent.effect
            embed.add_field(
                name=f"{talent.type}: {talent.name}",
                value=_value,
                inline=False,
            )
        if len(card.tags) > 0:
            embed.set_footer(text=f"標籤：{'、'.join([tag for tag in card.tags])}")
        return embed

    @classmethod
    def parse_action_card(cls, card: ActionCard) -> discord.Embed:
        """解析行動牌內容，傳回 discord.Embed"""
        description = ""
        if card.story_text is not None:
            description += f"{card.story_text}\n\n"
        description += f"花費：{cls._parse_costs(card.costs)}\n{card.effect}"
        embed = EmbedTemplate.normal(description, title=f"{card.name} ({card.type})")
        embed.set_image(url=card.image_url)

        if len(card.tags) > 0:
            embed.set_footer(text=f"標籤：{'、'.join([tag for tag in card.tags])}")
        return embed

    @classmethod
    def parse_summon(cls, card: Summon) -> discord.Embed:
        """解析召喚物內容，傳回 discord.Embed"""
        embed = EmbedTemplate.normal(card.effect, title=f"{card.name} ({card.type})")
        embed.set_image(url=card.image_url)
        return embed


class AchievemntParser:
    """成就"""

    @classmethod
    def parse_achievement(cls, achievement: Achievement) -> discord.Embed:
        """解析成就內容，傳回 discord.Embed"""
        description = f"類別：{achievement.group}\n"
        description += f"類型：{'隱藏成就' if achievement.ishidden else '一般成就'}\n"
        description += f"階段：{achievement.stages}"
        embed = EmbedTemplate.normal(description, title=achievement.name)
        for i, stage in enumerate(achievement.stage_details):
            embed.add_field(name=f"第 {i+1} 階段", value=stage.description)
        embed.set_footer(text=f"{achievement.version} 版本新增")
        return embed


class EquipmentParser:
    """裝備：聖遺物、武器"""

    @classmethod
    def parse_artifact(cls, artifact: Artifact) -> discord.Embed:
        """解析聖遺物內容，傳回 discord.Embed"""
        description = "稀有度：" + "、".join([str(r) for r in artifact.rarity]) + "\n"
        if artifact.effect_1pc is not None:
            description += f"效果：{artifact.effect_1pc}\n"
        if artifact.effect_2pc is not None:
            description += f"二件套：{artifact.effect_2pc}\n"
        if artifact.effect_4pc is not None:
            description += f"四件套：{artifact.effect_4pc}\n"
        embed = EmbedTemplate.normal(description, title=artifact.name)
        embed.set_thumbnail(url=artifact.images.flower_url or artifact.images.circlet_url)
        embed.set_footer(text=f"{artifact.version} 版本新增")
        return embed

    @classmethod
    def parse_artifact_part(cls, part: PartDetail) -> discord.Embed:
        """解析聖遺物部位內容，傳回 discord.Embed"""
        embed = EmbedTemplate.normal(part.description, title=part.name)
        embed.add_field(name="故事", value=part.story)
        embed.set_footer(text=part.relictype)
        return embed

    @classmethod
    def parse_weapon(cls, weapon: Weapon) -> discord.Embed:
        """解析武器內容，傳回 discord.Embed"""
        description = (
            f"基礎攻擊力：{weapon.base_atk}\n主屬性：{weapon.mainstat}+{weapon.mainvalue}\n"
        )
        embed = EmbedTemplate.normal(description, title=f"★{weapon.rarity} {weapon.name}")
        embed.add_field(name=weapon.effect_name, value=weapon.effect_desciption)
        embed.set_thumbnail(
            url=(
                weapon.images.awaken_icon_url
                or weapon.images.icon_url
                or API.get_image_url(weapon.images.icon)
            )
        )
        embed.set_footer(text=weapon.description)
        return embed


class CharacterParser:
    """角色：角色、天賦、命座"""

    @classmethod
    def parse_character(cls, character: Character) -> discord.Embed:
        """解析角色內容，傳回 discord.Embed"""
        embed = EmbedTemplate.normal(
            character.description, title=f"★{character.rarity} {character.name}"
        )
        if character.images is not None:
            embed.set_thumbnail(url=character.images.icon_url)
            if character.images.cover1_url is not None:
                embed.set_image(url=character.images.cover1_url)

        embed.add_field(
            name="屬性",
            value=(
                f"元素：{character.element}\n"
                + f"武器：{character.weapontype}\n"
                + f"突破：{character.substat}\n"
            ),
        )
        _text = f"性別：{character.gender}\n" + f"命座：{character.constellation}\n"
        if character.affiliation is not None:
            _text += f"隸屬：{character.affiliation}\n"
        if character.birthday is not None:
            _text += f"生日：{character.birthday}\n"
        embed.add_field(name="基本資料", value=_text)

        _cv = character.character_voice
        embed.add_field(
            name="聲優",
            value=f"中文：{_cv.chinese}\n"
            + f"日文：{_cv.japanese}\n"
            + f"英文：{_cv.english}\n"
            + f"韓文：{_cv.korean}\n",
            inline=False,
        )
        return embed

    @classmethod
    def parse_talent(cls, talent: Talent) -> discord.Embed:
        """解析角色天賦內容，傳回 discord.Embed"""
        embed = EmbedTemplate.normal("", title=talent.name)
        embed.add_field(name=talent.combat1.name, value=talent.combat1.description)
        embed.add_field(name="E：" + talent.combat2.name, value=talent.combat2.description)
        embed.add_field(name="Q：" + talent.combat3.name, value=talent.combat3.description)
        embed.add_field(name="固有：" + talent.passive1.name, value=talent.passive1.description)
        embed.add_field(name="固有：" + talent.passive2.name, value=talent.passive2.description)
        if talent.passive3 is not None:
            embed.add_field(
                name="固有：" + talent.passive3.name, value=talent.passive3.description
            )
        return embed

    @classmethod
    def parse_constellation(cls, constellation: Constellation) -> discord.Embed:
        """解析角色命座內容，傳回 discord.Embed"""
        cst = constellation
        embed = EmbedTemplate.normal("", title=cst.name)
        csts = [cst.c1, cst.c2, cst.c3, cst.c4, cst.c5, cst.c6]
        for i, _cst in enumerate(csts):
            embed.add_field(name=f"{i+1}命：{_cst.name}", value=_cst.description)
        return embed


class MaterialParser:
    """物品：食物、物品"""

    @classmethod
    def parse_food(cls, food: Food) -> discord.Embed:
        """解析食物內容，傳回 discord.Embed"""
        embed = EmbedTemplate.normal(food.description, title=food.name)
        embed.set_thumbnail(url=API.get_image_url(food.images.icon))
        if food.suspicious is not None:
            embed.add_field(name="失敗料理", value=food.suspicious.effect)
        if food.normal is not None:
            embed.add_field(name="普通料理", value=food.normal.effect)
        if food.delicious is not None:
            embed.add_field(name="完美料理", value=food.delicious.effect)
        embed.add_field(
            name="屬性",
            value=f"稀有度：{food.rarity}\n"
            + f"類型：{food.food_type}\n"
            + f"效果：{food.effect}\n",
        )
        embed.add_field(
            name="材料",
            value="\n".join([f"{ingred.name}：{ingred.count}" for ingred in food.ingredients]),
        )
        embed.set_footer(text=f"{food.version} 版本加入")
        return embed

    @classmethod
    def parse_material(cls, material: Material) -> discord.Embed:
        """解析物品內容，傳回 discord.Embed"""
        embed = EmbedTemplate.normal(material.description, title=material.name)
        embed.set_thumbnail(url=API.get_image_url(material.images.icon))

        embed.add_field(
            name="屬性",
            value=f"類型：{material.material_type}\n"
            + (f"稀有度：{material.rarity}\n" if material.rarity else "")
            + f"獲取來源：{'、'.join([s for s in material.sources])}\n",
        )

        if material.drop_domain is not None and material.days_of_week is not None:
            embed.add_field(
                name=material.drop_domain, value="\n".join([d for d in material.days_of_week])
            )
        if material.version is not None:
            embed.set_footer(text=f"{material.version} 版本加入")

        return embed
