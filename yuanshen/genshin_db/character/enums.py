import enum

from utility.emoji import emoji


class Element(enum.Enum):
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
