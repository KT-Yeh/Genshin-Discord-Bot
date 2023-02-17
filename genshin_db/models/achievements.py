from typing import Any, Dict, List

from pydantic import BaseModel, Field, root_validator

from .base import GenshinDbBase, GenshinDbListBase


class Reward(BaseModel):
    name: str
    count: int


class StageDetail(BaseModel):
    title: str
    progress: int
    raw_description: str = Field(alias="description")
    reward: Reward

    @property
    def description(self) -> str:
        # 將描述中的參數替換成實際數值
        return self.raw_description.replace("{param0}", str(self.progress))


class Achievement(GenshinDbBase):
    name: str
    group: str = Field(alias="achievementgroup")
    """此成就在哪個類別"""
    sortorder: int
    """排序 ID"""
    stages: int
    """此成就總共幾階段"""
    stage_details: List[StageDetail]
    """此成就每階段的細節"""

    ishidden: bool = False
    version: str
    """新增至遊戲當時的版本號碼"""

    @root_validator(pre=True)
    def combine_stage(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """將 stage 合併成 List"""
        stage_details = [data["stage1"]]
        if (stage2 := data.get("stage2")) is not None:
            stage_details.append(stage2)
        if (stage3 := data.get("stage3")) is not None:
            stage_details.append(stage3)
        data["stage_details"] = stage_details
        return data


class Achievements(GenshinDbListBase[Achievement]):
    __root__: List[Achievement]
