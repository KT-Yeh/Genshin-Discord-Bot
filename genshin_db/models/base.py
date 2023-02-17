from typing import Dict, Generic, List, TypeVar

from pydantic import BaseModel, PrivateAttr


class GenshinDbBase(BaseModel):
    """由 genshin-db 最高層物件 model 繼承"""

    name: str


T = TypeVar("T", bound=GenshinDbBase)


class GenshinDbListBase(BaseModel, Generic[T]):
    """由 genshin-db 最高層物件列表 model 繼承，提供依照名稱尋找特定物件的方法"""

    __root__: List[T]
    _name_item_dict: Dict[str, T] = PrivateAttr({})

    @property
    def list(self) -> List[T]:
        """所有物件列表"""
        return self.__root__

    def find(self, name: str) -> T | None:
        """依照名稱尋找特定物件"""
        if self._name_item_dict == {}:
            for item in self.list:
                self._name_item_dict[item.name] = item
        return self._name_item_dict.get(name)
