from datetime import datetime

from pydantic import BaseSettings


class Config(BaseSettings):
    """機器人的配置"""

    application_id: int = 0
    """機器人 Application ID，從 Discord Developer 網頁上取得"""
    test_server_id: int = 0
    """測試伺服器 ID，用來測試斜線指令，管理員指令只能在本伺服器使用"""
    bot_token: str = ""
    """機器人 Token，從 Discord Developer 網頁取得"""
    enka_api_key: str | None = None
    """向 Enka Network API 發送請求的金鑰"""

    schedule_daily_reward_time: int = 8
    """每日 Hoyolab 自動簽到的開始時間 (單位：時)"""
    notification_channel_id: list[int] = []
    """每日簽到完成後統計訊息欲發送到的 Discord 頻道 ID"""
    daily_reward_api_list: list[str] = []
    """遠端簽到 API URL list"""

    schedule_check_resin_interval: int = 10
    """自動檢查即時便箋的間隔 (單位：分鐘)"""
    schedule_loop_delay: float = 2.0
    """排程執行時每位使用者之間的等待間隔（單位：秒）"""
    game_maintenance_time: tuple[datetime, datetime] | None = None
    """遊戲的維護時間(起始, 結束)，在此期間內自動排程不會執行"""

    expired_user_days: int = 180
    """過期使用者天數，會刪除超過此天數未使用任何指令的使用者"""

    slash_cmd_cooldown: float = 5.0
    """使用者重複呼叫部分斜線指令的冷卻時間（單位：秒）"""
    discord_view_long_timeout: float = 1800
    """Discord 長時間互動介面（例：下拉選單） 的逾時時間（單位：秒）"""
    discord_view_short_timeout: float = 60
    """Discord 短時間互動介面（例：確認、選擇按鈕）的逾時時間（單位：秒）"""

    sentry_sdk_dsn: str | None = None
    """Sentry DSN 位址設定"""
    prometheus_server_port: int | None = None
    """Prometheus server 監聽的 Port，若為 None 表示不啟動 server"""
    geetest_solver_url: str | None = None
    """讓使用者設定圖形驗證的網址"""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()  # type: ignore
