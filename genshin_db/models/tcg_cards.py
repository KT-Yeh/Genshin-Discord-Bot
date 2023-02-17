from pydantic import BaseModel, Field, validator

from ..api import API
from .base import GenshinDbBase, GenshinDbListBase
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


class CharacterCard(GenshinDbBase):
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


class CharacterCards(GenshinDbListBase[CharacterCard]):
    __root__: list[CharacterCard]


class ActionCard(GenshinDbBase):
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


class ActionCards(GenshinDbListBase[ActionCard]):
    __root__: list[ActionCard]


class Summon(GenshinDbBase):
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


class Summons(GenshinDbListBase[Summon]):
    __root__: list[Summon]


class TCGCards:
    """七聖召喚卡牌資料封裝"""

    actions: ActionCards
    characters: CharacterCards
    summons: Summons

    def __init__(self, action_cards, character_cards, summons) -> None:
        self.actions = ActionCards.parse_obj(action_cards)
        self.characters = CharacterCards.parse_obj(character_cards)
        self.summons = Summons.parse_obj(summons)

    @property
    def list(self) -> list[ActionCard | CharacterCard | Summon]:
        """所有種類的卡牌列表"""
        return self.actions.list + self.characters.list + self.summons.list

    def find(self, item_name: str) -> ActionCard | CharacterCard | Summon | None:
        return (
            self.actions.find(item_name)
            or self.characters.find(item_name)
            or self.summons.find(item_name)
        )
