import enum


class Element(str, enum.Enum):
    """元素類型"""

    ANEMO = "ETWind"
    CRYO = "ETIce"
    DENDRO = "ETGrass"
    ELECTRO = "ETThunder"
    GEO = "ETRock"
    HYDRO = "ETWater"
    PYRO = "ETFire"

    def __str__(self) -> str:
        return {
            "ANEMO": "風",
            "CRYO": "冰",
            "DENDRO": "草",
            "ELECTRO": "雷",
            "GEO": "岩",
            "HYDRO": "水",
            "PYRO": "火",
        }.get(self.name, "")


class CostElement(str, enum.Enum):
    """骰子花費元素類型"""

    ENERGY = "1"
    """能量"""
    WHITE = "3"
    """相同元素"""
    BLACK = "10"
    """任意元素"""
    CRYO = "11"
    HYDRO = "12"
    PYRO = "13"
    ELECTRO = "14"
    GEO = "15"
    DENDRO = "16"
    ANEMO = "17"

    def __str__(self) -> str:
        return {
            "ENERGY": "能量",
            "WHITE": "相同元素",
            "BLACK": "任意元素",
            "CRYO": "冰元素",
            "HYDRO": "水元素",
            "PYRO": "火元素",
            "ELECTRO": "雷元素",
            "GEO": "岩元素",
            "DENDRO": "草元素",
            "ANEMO": "風元素",
        }.get(self.name, "")


class ActionType(str, enum.Enum):
    """行動牌類型"""

    EQUIPMENT = "AcEquip"
    """裝備牌"""
    EVENT = "AcEvent"
    """事件牌"""
    SUPPORT = "AcSupport"
    """支援牌"""

    def __str__(self) -> str:
        return {"EQUIPMENT": "裝備牌", "EVENT": "事件牌", "SUPPORT": "支援牌"}.get(self.name, "")
