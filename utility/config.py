import typing
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

class Config(BaseModel):
    application_id: int
    test_server_id: int
    bot_token: str
    enka_api_key: typing.Optional[str] = None
    auto_daily_reward_time: int = 8
    auto_check_resin_threshold: int = 150
    auto_loop_delay: float = 2.0
    slash_cmd_cooldown: float = 5.0
    discord_view_long_timeout: float = 1800
    discord_view_short_timeout: float = 60
    sentry_sdk_dsn: typing.Optional[str] = None
    game_maintenance_time: typing.Optional[typing.Tuple[datetime, datetime]] = None

config = Config.parse_file(Path('config.json'), encoding='utf8')