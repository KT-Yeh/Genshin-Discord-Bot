import discord
from .models import CharacterCard, ActionCard, DiceCost


def parse_costs(costs: list[DiceCost]) -> str:
    """解析骰子花費"""
    return " / ".join([f"{cost.element} ({cost.amount})" for cost in costs])


def parse_character_card(card: CharacterCard) -> discord.Embed:
    """解析角色牌內容，傳回 discord.Embed"""
    _description = f"屬性：{card.element}\n武器：{card.weapon}\n生命：{card.hp}\n"
    if len(card.belong_to) > 0 and card.belong_to[0] != "":
        _description += f"陣營：{card.belong_to[0]}"

    embed = discord.Embed(title=card.name, description=_description)
    embed.set_image(url=card.icon_url)

    for talent in card.talents:
        _value = "花費：" + parse_costs(talent.costs) + "\n"
        _value += talent.effect
        embed.add_field(name=f"{talent.name} ({talent.type})", value=_value, inline=False)

    return embed


def parse_action_card(card: ActionCard) -> discord.Embed:
    """解析行動牌內容，傳回 discord.Embed"""
    _description = (
        f"花費：{parse_costs(card.costs)}\n標籤："
        + "、".join([tag.text for tag in card.tags if tag.text != ""])
        + "\n"
        + card.effect
    )

    embed = discord.Embed(title=f"{card.name} ({card.type})", description=_description)
    embed.set_image(url=card.icon_url)

    return embed
