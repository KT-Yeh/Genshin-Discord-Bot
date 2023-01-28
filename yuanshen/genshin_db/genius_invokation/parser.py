import discord

from utility import EmbedTemplate, emoji

from .models import ActionCard, CharacterCard, DiceCost, Summon


def parse_costs(costs: list[DiceCost]) -> str:
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


def parse_character_card(card: CharacterCard) -> discord.Embed:
    """解析角色牌內容，傳回 discord.Embed"""
    embed = EmbedTemplate.normal(card.story_text, title=card.name)
    embed.set_image(url=card.image_url)
    for talent in card.talents:
        _value = "花費：" + parse_costs(talent.costs) + "\n"
        _value += talent.effect
        embed.add_field(
            name=f"{talent.type}: {talent.name}",
            value=_value,
            inline=False,
        )
    if len(card.tags) > 0:
        embed.set_footer(text=f"標籤：{'、'.join([tag for tag in card.tags])}")
    return embed


def parse_action_card(card: ActionCard) -> discord.Embed:
    """解析行動牌內容，傳回 discord.Embed"""
    description = ""
    if card.story_text is not None:
        description += f"{card.story_text}\n\n"
    description += f"花費：{parse_costs(card.costs)}\n{card.effect}"
    embed = EmbedTemplate.normal(description, title=f"{card.name} ({card.type})")
    embed.set_image(url=card.image_url)

    if len(card.tags) > 0:
        embed.set_footer(text=f"標籤：{'、'.join([tag for tag in card.tags])}")
    return embed


def parse_summon(card: Summon) -> discord.Embed:
    """解析召喚物內容，傳回 discord.Embed"""
    embed = EmbedTemplate.normal(card.effect, title=f"{card.name} ({card.type})")
    embed.set_image(url=card.image_url)
    return embed
