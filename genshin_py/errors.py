import genshin


class UserDataNotFound(Exception):
    """當機器人資料庫找不到使用者資料時的例外"""

    pass


class GenshinAPIException(Exception):
    """用來包裝 genshin.py 例外的例外

    Attributes
    -----
    origin: `genshin.GenshinException`
        從 genshin.py 拋出的例外
    message: `str`
        給機器人使用者的錯誤訊息
    """

    origin: genshin.GenshinException
    message: str = ""

    def __init__(self, exception: genshin.GenshinException, message: str) -> None:
        self.origin = exception
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.message} ({self.origin})"
