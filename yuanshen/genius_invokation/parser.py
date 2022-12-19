import discord
from .models import CharacterCard, ActionCard, DiceCost
from utility import emoji


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
    embed = discord.Embed(
        title=card.name,
        description=f"屬性：{card.element}\n武器：{card.weapon}\n生命：{card.hp}\n",
        color=0x5992C4,
    )
    embed.set_image(url=card.icon_url)
    if len(card.belong_to) > 0:
        embed.set_footer(text=f"陣營：{'、'.join(card.belong_to)}")

    for talent in card.talents:
        _value = "花費：" + parse_costs(talent.costs) + "\n"
        _value += talent.effect
        embed.add_field(name=f"{talent.name} ({talent.type})", value=_value, inline=False)

    return embed


def parse_action_card(card: ActionCard) -> discord.Embed:
    """解析行動牌內容，傳回 discord.Embed"""
    embed = discord.Embed(
        title=f"{card.name} ({card.type})",
        description=f"花費：{parse_costs(card.costs)}\n" + card.effect,
        color=0x5992C4,
    )
    if len(card.tags) > 0:
        embed.set_footer(text=f"標籤：{'、'.join([tag.text for tag in card.tags])}")
    embed.set_image(url=card.icon_url)

    return embed
