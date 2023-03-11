from typing import List, Optional

from pydantic import BaseModel, Field

from .base import GenshinDbBase, GenshinDbListBase


class AscendItem(BaseModel):
    name: str
    count: Optional[int] = None


class AscendCosts(BaseModel):
    ascend1: List[AscendItem]
    ascend2: List[AscendItem]
    ascend3: List[AscendItem]
    ascend4: List[AscendItem]
    ascend5: Optional[List[AscendItem]] = None
    ascend6: Optional[List[AscendItem]] = None


class Images(BaseModel):
    icon_url: Optional[str] = Field(None, alias="icon")
    awaken_icon_url: Optional[str] = Field(None, alias="awakenicon")

    icon: str = Field(alias="nameicon")
    gacha: str = Field(alias="namegacha")
    awakenicon: str = Field(alias="nameawakenicon")


class Weapon(GenshinDbBase):
    name: str
    description: str
    weapontype: str
    rarity: int
    story: str
    base_atk: int = Field(alias="baseatk")
    """初始基礎攻擊力"""
    substat: str
    subvalue: str
    effect_name: str = Field(alias="effectname")
    """武器特效名稱(標題)"""
    effect: str
    """武器特效敘述，需搭配 r1, r2, ..., r5 數值使用"""
    r1: List[str]
    r2: List[str]
    r3: List[str]
    r4: List[str]
    r5: List[str]
    ascend_costs: AscendCosts = Field(alias="costs")
    """突破所需素材"""
    images: Images
    version: str
    """新增至遊戲當時的版本號碼"""

    @property
    def effect_desciption(self) -> str:
        """取得包含精煉數值的武器特效敘述"""
        refines = [self.r1, self.r2, self.r3, self.r4, self.r5]
        nums = len(self.r1)  # 要填的數值數量
        refine_values: List[str] = []
        # 將 r1~r5 數值合併成一個 str，然後放入 refine_values
        for i in range(nums):
            refine_values.append(str(refines[0][i]))
            for j in range(1, 5):
                # 有些武器的最高精煉等級不同，所以要檢查
                if i < len(refines[j]):
                    refine_values[i] += f"/{refines[j][i]}"

        result = self.effect
        for i in range(nums):
            # 將 {0}, {1}... 替換成對應數值
            result = result.replace(f"{{{i}}}", refine_values[i])
        return result


class Weapons(GenshinDbListBase[Weapon]):
    __root__: List[Weapon]
