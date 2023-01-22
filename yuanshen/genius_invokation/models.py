from typing import Any, Dict, List

from pydantic import BaseModel, Field, root_validator, validator

from .enums import ActionType, CostElement, Element


class DiceCost(BaseModel):
    """骰子花費，包含花費數量與類型"""

    amount: int = Field(..., alias="cost_num")
    element: CostElement = Field(..., alias="cost_icon")


class Talent(BaseModel):
    """角色天賦技能"""

    id: int
    name: str
    effect: str = Field(..., alias="skill_text")
    costs: List[DiceCost] = Field(..., alias="skill_costs")
    type: str
    """A/E/Q/被動"""
    icon_url: str = Field(..., alias="resource")

    @validator("costs", pre=True)
    def remove_empty_cost(cls, costs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """將空的花費從 skill_costs 移除"""
        new_costs: List[Dict[str, str]] = []
        for cost in costs:
            if all(list(cost.values())):
                new_costs.append(cost)
        return new_costs

    @validator("type", pre=True)
    def remove_type_list(cls, type: List[str]) -> str:
        if len(type) > 0:
            return type[0]
        return ""


class CharacterCard(BaseModel):
    """角色牌"""

    id: int
    name: str
    element: Element = Field(..., alias="element_type")
    talents: List[Talent] = Field(..., alias="role_skill_infos")
    weapon: str
    belong_to: List[str]
    hp: int
    icon_url: str = Field(..., alias="resource")

    @validator("belong_to", pre=True)
    def remove_empty_belong_to(cls, belong_to: List[str]) -> List[str]:
        """將空的文字從 belong_to 移除"""
        return [_belong for _belong in belong_to if _belong != ""]


class ActionCardTag(BaseModel):
    """行動牌標籤"""

    id: str
    text: str


class ActionCard(BaseModel):
    """行動牌"""

    id: int
    name: str
    effect: str = Field(..., alias="content")
    type: ActionType = Field(..., alias="action_type")
    costs: List[DiceCost] = Field(..., alias="costs")
    tags: List[ActionCardTag] = Field(..., alias="action_card_tags")
    icon_url: str = Field(..., alias="resource")

    @root_validator(pre=True)
    def combine_dice_cost(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """將 cost_num1、cost_num2 合併成一個 list，與角色牌的格式一樣"""
        costs: List[Dict[str, str]] = []
        if bool(data["cost_num1"]) and bool(data["cost_type1_icon"]):
            costs.append({"cost_num": data["cost_num1"], "cost_icon": data["cost_type1_icon"]})
        if bool(data["cost_num2"]) and bool(data["cost_type2_icon"]):
            costs.append({"cost_num": data["cost_num2"], "cost_icon": data["cost_type2_icon"]})
        data["costs"] = costs
        return data

    @validator("tags", pre=True)
    def remove_empty_tag(cls, tags: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """將空的標籤從 action_card_tags 移除"""
        new_tags: List[Dict[str, str]] = []
        for tag in tags:
            if all(list(tag.values())):
                new_tags.append(tag)
        return new_tags


class Cards(BaseModel):
    """卡牌資料"""

    characters: List[CharacterCard] = Field(..., alias="role_card_infos")
    actions: List[ActionCard] = Field(..., alias="action_card_infos")


class TCGCards:
    """七聖召喚卡牌資料封裝"""

    characters: List[CharacterCard]
    actions: List[ActionCard]
    character_name_card: Dict[str, CharacterCard]
    action_name_card: Dict[str, ActionCard]

    def __init__(self, data: Dict) -> None:
        cards = Cards.parse_obj(data)
        self.characters = cards.characters
        self.actions = cards.actions
        self.character_name_card = {c.name: c for c in self.characters}
        self.action_name_card = {a.name: a for a in self.actions}
