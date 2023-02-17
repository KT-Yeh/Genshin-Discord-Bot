import enum

from utility.emoji import emoji


class Element(enum.Enum):
    """元素類型"""

    CRYO = "冰"
    HYDRO = "水"
    PYRO = "火"
    ELECTRO = "雷"
    GEO = "岩"
    DENDRO = "草"
    ANEMO = "風"
    VOID = "無"

    def __str__(self) -> str:
        return emoji.elements.get(self.name.lower(), str(self.value))


class CostElement(str, enum.Enum):
    """骰子花費元素類型"""

    ENERGY = "GCG_COST_ENERGY"
    """能量"""
    WHITE = "GCG_COST_DICE_SAME"
    """相同元素"""
    BLACK = "GCG_COST_DICE_VOID"
    """任意元素"""
    CRYO = "GCG_COST_DICE_CRYO"
    HYDRO = "GCG_COST_DICE_HYDRO"
    PYRO = "GCG_COST_DICE_PYRO"
    ELECTRO = "GCG_COST_DICE_ELECTRO"
    GEO = "GCG_COST_DICE_GEO"
    DENDRO = "GCG_COST_DICE_DENDRO"
    ANEMO = "GCG_COST_DICE_ANEMO"

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
