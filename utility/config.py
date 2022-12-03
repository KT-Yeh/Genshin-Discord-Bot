import typing
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel


class Config(BaseModel):
    """機器人的配置

    Attributes
    -----
    application_id: `int`
        機器人 Application ID，從 Discord Developer 網頁上取得
    test_server_id: `int`
        測試伺服器 ID，用來測試斜線指令，管理員指令只能在本伺服器使用
    bot_token: `str`
        機器人 Token，從 Discord Developer 網頁取得
    enka_api_key: `Optional[str]`
        向 Enka Network API 發送請求的金鑰
    schedule_daily_reward_time: `int`
        每日 Hoyolab 自動簽到的開始時間 (單位：時)
    schedule_check_resin_interval: `int`
        自動檢查即時便箋的間隔 (單位：分鐘)
    schedule_loop_delay: `float`
        排程執行時每位使用者之間的等待間隔（單位：秒）
    expired_user_days: `int`
        過期使用者天數，會刪除超過此天數未使用任何指令的使用者
    slash_cmd_cooldown: `float`
        使用者重複呼叫部分斜線指令的冷卻時間（單位：秒）
    discord_view_long_timeout: `float`
        Discord 長時間互動介面（例：下拉選單） 的逾時時間（單位：秒）
    discord_view_short_timeout: `float`
        Discord 短時間互動介面（例：確認、選擇按鈕）的逾時時間（單位：秒）
    database_file_path: `str`
        資料庫儲存的資料夾位置與檔名
    sentry_sdk_dsn: `Optional[str]`
        Sentry DSN 位址設定
    notification_channel_id: `Optional[int]`
        每日簽到完成後統計訊息欲發送到的 Discord 頻道 ID
    game_maintenance_time: `Optional[Tuple[datetime, datetime]]`
        遊戲的維護時間(起始, 結束)，在此期間內自動排程不會執行
    """

    application_id: int
    test_server_id: int
    bot_token: str
    enka_api_key: typing.Optional[str] = None
    schedule_daily_reward_time: int = 8
    schedule_check_resin_interval: int = 10
    schedule_loop_delay: float = 2.0
    expired_user_days: int = 30
    slash_cmd_cooldown: float = 5.0
    discord_view_long_timeout: float = 1800
    discord_view_short_timeout: float = 60
    database_file_path: str = "data/bot/bot.db"
    sentry_sdk_dsn: typing.Optional[str] = None
    notification_channel_id: typing.Optional[int] = None
    game_maintenance_time: typing.Optional[typing.Tuple[datetime, datetime]] = None


config = Config.parse_file(Path("config.json"), encoding="utf8")
