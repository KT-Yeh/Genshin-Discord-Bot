from pydantic import BaseModel, Field, validator

from ..api import API
from .enums import CostElement


class DiceCost(BaseModel):
    """骰子花費，包含花費數量與類型"""

    amount: int = Field(alias="count")
    element: CostElement = Field(alias="costtype")


class Images(BaseModel):
    normal: str = Field(alias="filename_cardface")
    """含卡牌外框"""
    golden: str = Field(alias="filename_cardface_golden")
    """含卡牌金框"""
    image: str = Field(alias="filename_cardface_HD")
    """純圖片"""


class Talent(BaseModel):
    """角色天賦技能"""

    id: int
    name: str
    effect: str = Field(alias="description")
    type: str
    """攻擊類型：A/E/Q/被動"""
    costs: list[DiceCost] = Field(alias="playcost")


class CharacterCard(BaseModel):
    """角色牌"""

    id: int
    name: str
    hp: int
    max_energy: int = Field(alias="maxenergy")
    tags: list[str] = Field(alias="tagstext")
    """含有元素屬性、武器、陣營"""
    story_title: str = Field(alias="storytitle")
    story_text: str = Field(alias="storytext")
    source: str
    """獲取此卡牌的來源方式"""
    talents: list[Talent] = Field(alias="skills")
    images: Images
    version: str
    """此卡牌加入遊戲時，當時的遊戲版本號碼"""

    @validator("story_text", pre=True)
    def remove_gender_tag(cls, v: str) -> str:
        return v.replace("{F#妳}{M#你}", "你")

    @property
    def image_url(self) -> str:
        return API.get_image_url(self.images.image)


class ActionCard(BaseModel):
    """行動牌"""

    id: int
    name: str
    type: str = Field(..., alias="cardtypetext")
    """卡牌類型 (裝備牌、事件牌、支援牌)"""
    tags: list[str] = Field(alias="tagstext")
    effect: str = Field(alias="description")
    story_title: str | None = Field(alias="storytitle")
    story_text: str | None = Field(alias="storytext")
    source: str | None
    """獲取此卡牌的來源方式"""
    costs: list[DiceCost] = Field(alias="playcost")
    images: Images
    version: str
    """此卡牌加入遊戲時，當時的遊戲版本號碼"""

    @validator("story_text", pre=True)
    def remove_gender_tag(cls, v: str) -> str:
        return v.replace("{F#妳}{M#你}", "你")

    @property
    def image_url(self) -> str:
        return API.get_image_url(self.images.image)


class Summon(BaseModel):
    """召喚物"""

    id: int
    name: str
    type: str = Field(alias="cardtypetext")
    """類型 (召喚物)"""
    effect: str = Field(alias="description")
    images: Images
    version: str
    """此卡牌加入遊戲時，當時的遊戲版本號碼"""

    @property
    def image_url(self) -> str:
        return API.get_image_url(self.images.image)


class TCGCards(BaseModel):
    """七聖召喚卡牌資料封裝"""

    actions: list[ActionCard]
    characters: list[CharacterCard]
    summons: list[Summon]

    _name_card_dict: dict[str, ActionCard | CharacterCard | Summon] = {}

    class Config:
        underscore_attrs_are_private = True  # 將名字 _ 開頭的視為私有屬性，不做驗證

    def __init__(self, action_cards, character_cards, summons) -> None:
        data = {"actions": action_cards, "characters": character_cards, "summons": summons}
        super().__init__(**data)

    @property
    def all_cards(self) -> list[ActionCard | CharacterCard | Summon]:
        """所有種類的卡牌列表"""
        return self.actions + self.characters + self.summons

    def find_card(self, name: str) -> ActionCard | CharacterCard | Summon | None:
        """依照名稱尋找特定卡牌"""
        # 利用 dict 尋找特定卡牌，在第一次時先建立字典
        if self._name_card_dict == {}:
            for card in self.all_cards:
                self._name_card_dict[card.name] = card

        return self._name_card_dict.get(name)
