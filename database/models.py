import datetime
import json
import typing
import zlib

import genshin
import sqlalchemy
from mihomo import StarrailInfoParsed
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

from .dataclass import spiral_abyss


class Base(MappedAsDataclass, DeclarativeBase):
    """資料庫 Table 基礎類別，繼承自 sqlalchemy `MappedAsDataclass`, `DeclarativeBase`"""

    type_annotation_map = {dict[str, str]: sqlalchemy.JSON}


class User(Base):
    """使用者資料庫 Table"""

    __tablename__ = "users"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """使用者 Discord ID"""
    last_used_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """使用者最後一次成功使用機器人指令的時間"""

    cookie_default: Mapped[str | None] = mapped_column(default=None)
    """當特定遊戲的 cookie 未設定時，則使用此欄位的 cookie"""
    cookie_genshin: Mapped[str | None] = mapped_column(default=None)
    """用來給原神指令使用的 Hoyolab 或米游社網頁的 Cookie"""
    cookie_honkai3rd: Mapped[str | None] = mapped_column(default=None)
    """用來給崩壞3指令使用的 Hoyolab 或米游社網頁的 Cookie"""
    cookie_starrail: Mapped[str | None] = mapped_column(default=None)
    """用來給星穹鐵道指令使用的 Hoyolab 或米游社網頁的 Cookie"""
    cookie_themis: Mapped[str | None] = mapped_column(default=None)
    """用來給未定事件簿指令使用的 Hoyolab 或米游社網頁的 Cookie"""
    cookie_zzz: Mapped[str | None] = mapped_column(default=None)
    """用來給絕區零指令使用的 Hoyolab 或米游社網頁的 Cookie"""

    uid_genshin: Mapped[int | None] = mapped_column(default=None)
    """原神角色的 UID"""
    uid_honkai3rd: Mapped[int | None] = mapped_column(default=None)
    """崩壞3角色的 UID"""
    uid_starrail: Mapped[int | None] = mapped_column(default=None)
    """星穹鐵道角色的 UID"""
    uid_zzz: Mapped[int | None] = mapped_column(default=None)
    """絕區零角色的 UID"""


class ScheduleDailyCheckin(Base):
    """排程每日自動簽到資料庫 Table"""

    __tablename__ = "schedule_daily_checkin"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """使用者 Discord ID"""
    discord_channel_id: Mapped[int]
    """發送通知訊息的 Discord 頻道的 ID"""
    is_mention: Mapped[bool]
    """發送訊息時是否要 tag 使用者"""
    next_checkin_time: Mapped[datetime.datetime]
    """下次簽到的時間 (使用者設定每日要簽到的時間)"""

    has_genshin: Mapped[bool] = mapped_column(default=False)
    """是否要簽到原神"""
    has_honkai3rd: Mapped[bool] = mapped_column(default=False)
    """是否要簽到崩壞3"""
    has_starrail: Mapped[bool] = mapped_column(default=False)
    """是否要簽到星穹鐵道"""
    has_themis: Mapped[bool] = mapped_column(default=False)
    """是否要簽到未定事件簿(國際服)"""
    has_themis_tw: Mapped[bool] = mapped_column(default=False)
    """是否要簽到未定事件簿(台服)"""
    has_zzz: Mapped[bool] = mapped_column(default=False)
    """是否要簽到絕區零"""

    def update_next_checkin_time(self) -> None:
        """將下次簽到時間更新為明日"""
        dt = datetime.datetime
        self.next_checkin_time = dt.combine(
            dt.now().date(), self.next_checkin_time.time()
        ) + datetime.timedelta(days=1)


class GeetestChallenge(Base):
    """用在簽到圖形驗證 Geetest 的 Challenge 值"""

    __tablename__ = "geetest_challenge"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """使用者 Discord ID"""

    genshin: Mapped[dict[str, str] | None] = mapped_column(default=None)
    """原神 challenge 值"""
    honkai3rd: Mapped[dict[str, str] | None] = mapped_column(default=None)
    """崩壞3 challenge 值"""
    starrail: Mapped[dict[str, str] | None] = mapped_column(default=None)
    """星穹鐵道 challenge 值"""


class GenshinScheduleNotes(Base):
    """原神排程自動檢查即時便箋資料庫 Table"""

    __tablename__ = "genshin_schedule_notes"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """使用者 Discord ID"""
    discord_channel_id: Mapped[int]
    """發送通知訊息的 Discord 頻道的 ID"""
    next_check_time: Mapped[datetime.datetime | None] = mapped_column(
        insert_default=sqlalchemy.func.now(), default=None
    )
    """下次檢查的時間，當檢查時超過此時間才會對 Hoyolab 請求資料"""

    threshold_resin: Mapped[int | None] = mapped_column(default=None)
    """樹脂額滿之前幾小時發送提醒"""
    threshold_currency: Mapped[int | None] = mapped_column(default=None)
    """洞天寶錢額滿之前幾小時發送提醒"""
    threshold_transformer: Mapped[int | None] = mapped_column(default=None)
    """質變儀完成之前幾小時發送提醒"""
    threshold_expedition: Mapped[int | None] = mapped_column(default=None)
    """全部派遣完成之前幾小時發送提醒"""
    check_commission_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """下次檢查今天的委託任務還未完成的時間"""


class GenshinSpiralAbyss(Base):
    """原神深境螺旋資料庫 Table"""

    __tablename__ = "genshin_spiral_abyss"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """使用者 Discord ID"""
    season: Mapped[int] = mapped_column(primary_key=True)
    """深淵期數"""
    _abyss_raw_data: Mapped[bytes] = mapped_column(init=False)
    """深淵 bytes 資料"""
    _characters_raw_data: Mapped[bytes | None] = mapped_column(init=False, default=None)
    """角色 bytes 資料"""

    def __init__(
        self,
        discord_id: int,
        season: int,
        abyss: genshin.models.SpiralAbyss,
        characters: typing.Sequence[genshin.models.Character] | None = None,
    ):
        """
        初始化原神深境螺旋資料庫表的物件。

        Parameters
        ------
        discord_id: `int`
            使用者 Discord ID
        season: `int`
            深淵期數
        abyss: `genshin.models.SpiralAbyss`
            genshin.py 深境螺旋資料。
        characters `Sequence[genshin.models.Character]` | `None`:
            genshin.py 角色資料。預設為 None。
        """
        self.discord_id = discord_id
        self.season = season

        json_str = abyss.json(by_alias=True)
        self._abyss_raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

        if characters is not None:
            # 將 genshin.py 的角色資料轉換為自定義的 dataclass，以減少資料大小
            # 然後轉換成 json -> byte -> 壓縮 -> 保存
            _characters = [spiral_abyss.CharacterData.from_orm(c) for c in characters]
            json_str = ",".join([c.json() for c in _characters])
            json_str = "[" + json_str + "]"
            self._characters_raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def abyss(self) -> genshin.models.SpiralAbyss:
        """genshin.py 深境螺旋資料"""
        data = zlib.decompress(self._abyss_raw_data).decode("utf-8")
        return genshin.models.SpiralAbyss.parse_raw(data)

    @property
    def characters(self) -> list[spiral_abyss.CharacterData] | None:
        """深淵角色資料"""
        if self._characters_raw_data is None:
            return None
        data = zlib.decompress(self._characters_raw_data).decode("utf-8")
        listobj: list = json.loads(data)
        return [spiral_abyss.CharacterData.parse_obj(c) for c in listobj]


class GenshinShowcase(Base):
    """原神角色展示櫃資料庫 Table"""

    __tablename__ = "genshin_showcases"

    uid: Mapped[int] = mapped_column(primary_key=True)
    """原神 UID"""
    _raw_data: Mapped[bytes]
    """展示櫃 bytes 資料"""

    def __init__(self, uid: int, data: dict[str, typing.Any]):
        """初始化原神角色展示櫃資料表的物件

        Parameters
        ------
        uid: `int`
            原神 UID
        data: `dict[str, Any]`
            Enka network API 的 JSON 格式資料
        """
        # 將 dict 物件轉成 json -> byte -> 壓縮 -> 保存
        json_str = json.dumps(data)
        self.uid = uid
        self._raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def data(self) -> dict[str, typing.Any]:
        """Enka network API 的 JSON 格式資料"""
        data = zlib.decompress(self._raw_data).decode("utf-8")
        return json.loads(data)


class StarrailScheduleNotes(Base):
    """星穹鐵道排程自動檢查即時便箋資料庫 Table"""

    __tablename__ = "starrail_schedule_notes"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """使用者 Discord ID"""
    discord_channel_id: Mapped[int]
    """發送通知訊息的 Discord 頻道的 ID"""
    next_check_time: Mapped[datetime.datetime | None] = mapped_column(
        insert_default=sqlalchemy.func.now(), default=None
    )
    """下次檢查的時間，當檢查時超過此時間才會對 Hoyolab 請求資料"""

    threshold_power: Mapped[int | None] = mapped_column(default=None)
    """開拓力額滿之前幾小時發送提醒"""
    threshold_expedition: Mapped[int | None] = mapped_column(default=None)
    """全部委託完成之前幾小時發送提醒"""
    check_daily_training_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """下次檢查今天的每日實訓還未完成的時間"""
    check_universe_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """下次檢查本周的模擬宇宙還未完成的時間"""
    check_echoofwar_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """下次檢查本周的歷戰餘響還未完成的時間"""


class StarrailForgottenHall(Base):
    """星穹鐵道忘卻之庭資料庫 Table"""

    __tablename__ = "starrail_forgotten_hall"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """使用者 Discord ID"""
    season: Mapped[int] = mapped_column(primary_key=True)
    """忘卻之庭期數"""
    _raw_data: Mapped[bytes] = mapped_column()
    """忘卻之庭 bytes 資料"""

    def __init__(self, discord_id: int, season: int, data: genshin.models.StarRailChallenge):
        """初始化星穹鐵道忘卻之庭資料表的物件。

        Parameters:
        ------
        discord_id: `int`
            使用者 Discord ID。
        season: `int`
            忘卻之庭期數。
        data: `genshin.models.StarRailChallenge`
            genshin.py 忘卻之庭資料。
        """
        json_str = data.json(by_alias=True, ensure_ascii=False)
        self.discord_id = discord_id
        self.season = season
        self._raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def data(self) -> genshin.models.StarRailChallenge:
        """genshin.py 忘卻之庭資料"""
        data = zlib.decompress(self._raw_data).decode("utf-8")
        return genshin.models.StarRailChallenge.parse_raw(data)


class StarrailPureFiction(Base):
    """星穹鐵道虛構敘事資料庫 Table"""

    __tablename__ = "starrail_pure_fiction"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """使用者 Discord ID"""
    season: Mapped[int] = mapped_column(primary_key=True)
    """虛構敘事期數"""
    _raw_data: Mapped[bytes] = mapped_column()
    """虛構敘事 bytes 資料"""

    def __init__(self, discord_id: int, season: int, data: genshin.models.StarRailPureFiction):
        """初始化星穹鐵道虛構敘事資料表的物件。

        Parameters:
        ------
        discord_id: `int`
            使用者 Discord ID。
        season: `int`
            虛構敘事期數。
        data: `genshin.models.StarRailPureFiction`
            genshin.py 虛構敘事資料。
        """
        json_str = data.json(by_alias=True, ensure_ascii=False)
        self.discord_id = discord_id
        self.season = season
        self._raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def data(self) -> genshin.models.StarRailPureFiction:
        """genshin.py 虛構敘事資料"""
        data = zlib.decompress(self._raw_data).decode("utf-8")
        return genshin.models.StarRailPureFiction.parse_raw(data)


class StarrailShowcase(Base):
    """星穹鐵道展示櫃資料庫 Table"""

    __tablename__ = "starrail_showcases"

    uid: Mapped[int] = mapped_column(primary_key=True)
    """星穹鐵道 UID"""
    _raw_data: Mapped[bytes]
    """展示櫃 bytes 資料"""

    def __init__(self, uid: int, data: StarrailInfoParsed):
        """初始化星穹鐵道展示櫃資料表的物件。

        Parameters:
        ------
        uid: `int`
            星穹鐵道 UID。
        data: `StarrailInfoParsed`
            Mihomo API 資料。
        """
        json_str = data.json(by_alias=True)
        self.uid = uid
        self._raw_data = zlib.compress(json_str.encode("utf-8"), level=5)

    @property
    def data(self) -> StarrailInfoParsed:
        """Mihomo API 資料"""
        data = zlib.decompress(self._raw_data).decode("utf-8")
        return StarrailInfoParsed.parse_raw(data)


class ZZZScheduleNotes(Base):
    """絕區零排程自動檢查即時便箋資料庫 Table"""

    __tablename__ = "zzz_schedule_notes"

    discord_id: Mapped[int] = mapped_column(primary_key=True)
    """使用者 Discord ID"""
    discord_channel_id: Mapped[int]
    """發送通知訊息的 Discord 頻道的 ID"""
    next_check_time: Mapped[datetime.datetime | None] = mapped_column(
        insert_default=sqlalchemy.func.now(), default=None
    )
    """下次檢查的時間，當檢查時超過此時間才會對 Hoyolab 請求資料"""

    threshold_battery: Mapped[int | None] = mapped_column(default=None)
    """電量額滿之前幾小時發送提醒"""
    check_daily_engagement_time: Mapped[datetime.datetime | None] = mapped_column(default=None)
    """下次檢查今天的每日活躍還未完成的時間"""
