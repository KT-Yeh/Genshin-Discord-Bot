import typing
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

class Config(BaseModel):
    application_id: int
    test_server_id: int
    bot_token: str
    enka_api_key: typing.Optional[str] = None
    schedule_daily_reward_time: int = 8
    schedule_check_resin_threshold: int = 150
    schedule_loop_delay: float = 2.0
    expired_user_days: int = 30
    slash_cmd_cooldown: float = 5.0
    discord_view_long_timeout: float = 1800
    discord_view_short_timeout: float = 60
    database_file_path: str = 'data/bot.db'
    sentry_sdk_dsn: typing.Optional[str] = None
    notification_channel_id: typing.Optional[int] = None
    game_maintenance_time: typing.Optional[typing.Tuple[datetime, datetime]] = None

config = Config.parse_file(Path('config.json'), encoding='utf8')