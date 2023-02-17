from dataclasses import dataclass

from .achievements import Achievement, Achievements
from .artifacts import Artifact, Artifacts
from .base import GenshinDbBase, GenshinDbListBase
from .characters import Character, Characters
from .constellations import Constellation, Constellations
from .foods import Food, Foods
from .materials import Material, Materials
from .talents import Talent, Talents
from .tcg_cards import ActionCard, CharacterCard, Summon, TCGCards
from .weapons import Weapon, Weapons

GenshinDbItem = (
    Achievement
    | Artifact
    | Character
    | Constellation
    | Food
    | Material
    | Talent
    | ActionCard
    | CharacterCard
    | Summon
    | Weapon
)


@dataclass
class GenshinDbAllData:
    """將 genshin db 所有資料封裝"""

    achievements: Achievements
    artifacts: Artifacts
    characters: Characters
    constellations: Constellations
    foods: Foods
    materials: Materials
    talents: Talents
    tcg_cards: TCGCards
    weapons: Weapons

    def find(self, item_name: str) -> GenshinDbItem | None:
        return (
            self.achievements.find(item_name)
            or self.tcg_cards.find(item_name)
            or self.weapons.find(item_name)
            or self.foods.find(item_name)
            or self.materials.find(item_name)
            or self.artifacts.find(item_name)
            or self.characters.find(item_name)
            or self.constellations.find(item_name)
            or self.talents.find(item_name)
        )
