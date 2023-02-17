import enum
from typing import Any, ClassVar, Union

import aiohttp


class API:
    """genshin-db api，能夠取得遊戲內容 json 格式資料"""

    GENSHIN_DB_URL: ClassVar[str] = "https://genshin-db-api.vercel.app/api/{folder}"
    IMAGE_URL: ClassVar[
        str
    ] = "https://res.cloudinary.com/genshin/image/upload/sprites/{image}.png"

    class GenshinDBLang(enum.Enum):
        """genshin-db api 支援的語言: https://genshin-db-api.vercel.app/api/languages"""

        CHT = "ChineseTraditional"
        CHS = "ChineseSimplified"
        ENG = "English"

    class GenshinDBFolder(enum.Enum):
        """genshin-db api 能夠搜尋的資料夾: https://github.com/theBowja/genshin-db/wiki/Folders"""

        TCG_ACTION_CARDS = "tcgactioncards"
        TCG_CHARACTER_CARDS = "tcgcharactercards"
        TCG_SUMMONS = "tcgsummons"

        CHARACTERS = "characters"
        CONSTELLATIONS = "constellations"
        TALENTS = "talents"

        ACHIEVEMENTS = "achievements"
        ARTIFACTS = "artifacts"
        FOODS = "foods"
        MATERIALS = "materials"
        WEAPONS = "weapons"

    @classmethod
    async def request_genshin_db(
        cls,
        folder: Union[GenshinDBFolder, str],
        query: str,
        *,
        dumpResult: bool = False,
        matchNames: bool = True,
        matchAltNames: bool = True,
        matchAliases: bool = False,
        matchCategories: bool = False,
        verboseCategories: bool = False,
        queryLanguages: str = GenshinDBLang.CHT.value,
        resultLanguage: str = GenshinDBLang.CHT.value,
    ) -> Any:
        """向 genshin-db api 請求資料，回傳 json 格式資料

        Parameters
        ------
        folder: `GenshinDBFolder` | `str`
            參考 https://github.com/theBowja/genshin-db/wiki/Folders
        query: `str`
            範例參考 https://github.com/theBowja/genshin-db/blob/main/examples/examples.md
        other options: `keyword arguments`
            其他參數說明: https://github.com/theBowja/genshin-db/wiki/Query-Options

        Returns
        ------
        `typing.Any`:
            json 格式的資料
        """
        folder_name = str(folder.value) if not isinstance(folder, str) else folder
        url = cls.GENSHIN_DB_URL.format(folder=folder_name)
        params = {
            "query": query,
            "dumpResult": str(dumpResult),
            "matchNames": str(matchNames),
            "matchAltNames": str(matchAltNames),
            "matchAliases": str(matchAliases),
            "matchCategories": str(matchCategories),
            "verboseCategories": str(verboseCategories),
            "queryLanguages": queryLanguages,
            "resultLanguage": resultLanguage,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"無法取得 genshin-db api 內容: url={url} params={str(params)}")
                data = await response.json(encoding="utf-8")
                return data

    @classmethod
    def get_image_url(cls, image_name: str) -> str:
        """針對 UI_xxxxx 的遊戲圖片檔案，取得線上資源連結

        Parameters
        ------
        image_name: `str`
            以 `UI_xxxx` 為格式的圖片名稱

        Returns
        ------
        `str`:
            此圖片的線上 URL 連結
        """
        return cls.IMAGE_URL.format(image=image_name)
